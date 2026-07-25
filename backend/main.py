import base64
import json
import asyncio
import re
import os
import shutil
from datetime import datetime, timezone
import aiohttp
from websockets.asyncio.server import serve

BASE_DIR = "/home/matteo/scratchFiles/"
USER_DATA_DIR = BASE_DIR + "userData/"
REPOS_DIR = BASE_DIR + "repos/"
SESSIONS_FILE = BASE_DIR + "sessions.json"
REPOS_DB_FILE = BASE_DIR + "repos.json"

_db_lock = asyncio.Lock()


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def _write_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(value, f, indent=2)


async def save_session(token, username, session_id):
    async with _db_lock:
        sessions = _read_json(SESSIONS_FILE, {})
        sessions[token] = {"username": username, "session_id": session_id}
        _write_json(SESSIONS_FILE, sessions)


async def get_session(token):
    async with _db_lock:
        sessions = _read_json(SESSIONS_FILE, {})
        return sessions.get(token)


async def get_username(token):
    session = await get_session(token)
    return session["username"] if session else None


async def get_repos_db():
    async with _db_lock:
        return _read_json(REPOS_DB_FILE, {})


async def set_user_repo(username, project_id, entry):
    async with _db_lock:
        db = _read_json(REPOS_DB_FILE, {})
        db.setdefault(username, {})[str(project_id)] = entry
        _write_json(REPOS_DB_FILE, db)


async def remove_user_repo(username, project_id):
    async with _db_lock:
        db = _read_json(REPOS_DB_FILE, {})
        db.get(username, {}).pop(str(project_id), None)
        _write_json(REPOS_DB_FILE, db)


def repo_dir(username, project_id):
    return os.path.join(REPOS_DIR, username, str(project_id))


async def run_git(*args, cwd):
    proc = await asyncio.create_subprocess_exec(
        "git", *args, cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr.decode().strip()}")
    return stdout.decode()


async def fetch_scratch_project_info(username, session_id, project_id):
    """Best-effort lookup of a project's own metadata (title, isPublished, dateOfCreation)."""
    headers = {
        "x-csrftoken": "a",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": f"scratchsessionsid={session_id};scratchcsrftoken=a;scratchlanguage=en;",
        "referer": "https://scratch.mit.edu",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.scratch.mit.edu/users/{username}/projects/{project_id}", headers=headers) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return {
                "id": str(project_id),
                "name": data.get("title", f"Project {project_id}"),
                "isPublished": bool(data.get("public", data.get("isPublished", False))),
                "dateOfCreation": data.get("history", {}).get("created"),
                "project_token": data.get("project_token"),
            }


async def fetch_scratch_project_list(username, session_id):
    """Best-effort listing of every project owned by the user (published or not)."""
    headers = {
        "x-csrftoken": "a",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": f"scratchsessionsid={session_id};scratchcsrftoken=a;scratchlanguage=en;",
        "referer": "https://scratch.mit.edu",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    }
    projects = []
    async with aiohttp.ClientSession() as session:
        async with session.get("https://scratch.mit.edu/site-api/projects/all/1/", headers=headers) as resp:
            if resp.status != 200:
                return projects
            raw = await resp.json()
            for entry in raw:
                fields = entry.get("fields", entry)
                pk = entry.get("pk", fields.get("id"))
                if pk is None:
                    continue
                projects.append({
                    "id": str(pk),
                    "name": fields.get("title", f"Project {pk}"),
                    "isPublished": bool(fields.get("isPublished", False)),
                    "dateOfCreation": fields.get("datetime_created"),
                })
    return projects


async def fetch_scratch_project_data(project_id, project_token=None):
    async with aiohttp.ClientSession() as session:
        url = f"https://projects.scratch.mit.edu/{project_id}"
        if project_token:
            url += f"?token={project_token}"
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Could not fetch project {project_id} data (status {resp.status})")
            return await resp.json()


async def login(id_, username, password):
    headers = {
        "x-csrftoken": "a",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": "scratchcsrftoken=a;scratchlanguage=en;",
        "referer": "https://scratch.mit.edu",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "username": username,
        "password": password,
        "useMessages": True,
    })

    async with aiohttp.ClientSession() as session:
        async with session.post("https://scratch.mit.edu/login/", data=body, headers=headers) as resp:
            try:
                result = (await resp.json())[0]
            except Exception as e:
                print(e)
                return {"success": False, "error": "unexpected_response"}

            if result.get("success") != 1:
                return {"success": False, "error": "invalid_credentials"}

            session_cookie = resp.cookies.get("scratchsessionsid")

    session_id = session_cookie.value if session_cookie else None
    token = result.get("token")

    data = {
        "username": username,
        "password": password,
        "session_id": session_id,
        "token": token,
    }

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with open(USER_DATA_DIR + "user.json", "w") as file:
        json.dump(data, file, indent=2)

    if token:
        await save_session(token, username, session_id)

    return {
        "success": True,
        "username": username,
        "session_id": session_id,
        "token": token,
    }

async def repoCreate(id_, token=None, projectId=None, **kwargs):
    session = await get_session(token)
    if not session:
        return {"success": False, "error": "unauthorized"}
    if not projectId:
        return {"success": False, "error": "missing_project_id"}

    username = session["username"]
    path = repo_dir(username, projectId)

    if os.path.isdir(path):
        return {"success": True, "projectId": projectId}

    try:
        info = await fetch_scratch_project_info(username, session["session_id"], projectId)
        project_data = await fetch_scratch_project_data(projectId, info.get("project_token") if info else None)
    except Exception as e:
        print(e)
        return {"success": False, "error": "fetch_failed"}

    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "project.json"), "w") as f:
        json.dump(project_data, f, indent=2)

    await run_git("init", cwd=path)
    await run_git("add", "project.json", cwd=path)
    await run_git("-c", "user.name=MVC", "-c", "user.email=mvc@local", "commit", "-m", "Initial version", cwd=path)

    entry = {
        "name": (info or {}).get("name", f"Project {projectId}"),
        "isPublished": (info or {}).get("isPublished", False),
        "dateOfCreation": (info or {}).get("dateOfCreation") or datetime.now(timezone.utc).isoformat(),
    }
    await set_user_repo(username, projectId, entry)

    return {"success": True, "projectId": projectId}

async def repoCreateOK(id_, **kwargs):
    return {"success": True}

async def repoDelete(id_, token=None, projectId=None, **kwargs):
    session = await get_session(token)
    if not session:
        return {"success": False, "error": "unauthorized"}
    if not projectId:
        return {"success": False, "error": "missing_project_id"}

    username = session["username"]
    path = repo_dir(username, projectId)

    shutil.rmtree(path, ignore_errors=True)
    await remove_user_repo(username, projectId)

    return {"success": True}

async def repoDeleteOK(id_, **kwargs):
    return {"success": True}

async def repoCommit(id_, token=None, projectId=None, **kwargs):
    session = await get_session(token)
    if not session:
        return {"success": False, "error": "unauthorized"}
    if not projectId:
        return {"success": False, "error": "missing_project_id"}

    username = session["username"]
    path = repo_dir(username, projectId)
    if not os.path.isdir(path):
        return {"success": False, "error": "not_found"}

    try:
        info = await fetch_scratch_project_info(username, session["session_id"], projectId)
        project_data = await fetch_scratch_project_data(projectId, info.get("project_token") if info else None)
    except Exception as e:
        print(e)
        return {"success": False, "error": "fetch_failed"}

    with open(os.path.join(path, "project.json"), "w") as f:
        json.dump(project_data, f, indent=2)

    await run_git("add", "project.json", cwd=path)
    status = await run_git("status", "--porcelain", cwd=path)
    if not status.strip():
        return {"success": True, "projectId": projectId, "changed": False}

    message = f"Snapshot {datetime.now(timezone.utc).isoformat()}"
    await run_git("-c", "user.name=MVC", "-c", "user.email=mvc@local", "commit", "-m", message, cwd=path)
    commit_hash = (await run_git("rev-parse", "HEAD", cwd=path)).strip()

    if info:
        await set_user_repo(username, projectId, {
            "name": info.get("name", f"Project {projectId}"),
            "isPublished": info.get("isPublished", False),
            "dateOfCreation": info.get("dateOfCreation") or datetime.now(timezone.utc).isoformat(),
        })

    return {"success": True, "projectId": projectId, "changed": True, "commit": commit_hash}

async def repoCommitOK(id_, **kwargs):
    return {"success": True}

async def repoGetData(id_, token=None, projectId=None, **kwargs):
    session = await get_session(token)
    if not session:
        return {"success": False, "error": "unauthorized"}
    if not projectId:
        return {"success": False, "error": "missing_project_id"}

    username = session["username"]
    path = repo_dir(username, projectId)
    if not os.path.isdir(path):
        return {"success": False, "error": "not_found"}

    db = await get_repos_db()
    entry = db.get(username, {}).get(str(projectId), {})

    log = await run_git("log", "--pretty=format:%H|%ad|%s", "--date=iso-strict", cwd=path)
    commits = []
    for line in log.splitlines():
        commit_hash, date, message = line.split("|", 2)
        commits.append({"commit": commit_hash, "date": date, "message": message})

    project = {
        "id": str(projectId),
        "name": entry.get("name", f"Project {projectId}"),
        "created": True,
        "isPublished": entry.get("isPublished", False),
        "dateOfCreation": entry.get("dateOfCreation"),
    }

    return {"success": True, "project": project, "commits": commits}

async def repoGetDataResponse(id_, **kwargs):
    return {"success": True}

async def getRepoList(id_, token=None, **kwargs):
    session = await get_session(token)
    if not session:
        return {"success": False, "error": "unauthorized"}

    username = session["username"]
    db = await get_repos_db()
    created_ids = db.get(username, {})

    try:
        remote_projects = await fetch_scratch_project_list(username, session["session_id"])
    except Exception as e:
        print(e)
        remote_projects = []

    projects = []
    seen_ids = set()
    for proj in remote_projects:
        seen_ids.add(proj["id"])
        tracked = created_ids.get(proj["id"])
        projects.append({
            "id": proj["id"],
            "name": tracked["name"] if tracked else proj["name"],
            "created": proj["id"] in created_ids,
            "isPublished": proj["isPublished"],
            "dateOfCreation": proj["dateOfCreation"],
        })

    # Include tracked repos even if they no longer show up in the remote listing.
    for project_id, tracked in created_ids.items():
        if project_id in seen_ids:
            continue
        projects.append({
            "id": project_id,
            "name": tracked.get("name", f"Project {project_id}"),
            "created": True,
            "isPublished": tracked.get("isPublished", False),
            "dateOfCreation": tracked.get("dateOfCreation"),
        })

    return {"success": True, "projects": projects}

funcs = {
    "L": login,
    "RC": repoCreate,
    "RCOK": repoCreateOK,
    "RD": repoDelete,
    "RDOK": repoDeleteOK,
    "RCM": repoCommit,
    "RCMOK": repoCommitOK,
    "RGD": repoGetData,
    "RGDR": repoGetDataResponse,
    "GRL": getRepoList
}

async def recieve(websocket):
    async for message in websocket:
        data = json.loads(message)
        id_ = data.get("id_")
        if not id_ or not isinstance(id_, str):
            print("Missing or invalid 'id_' in message:", data)
            await websocket.send(json.dumps({"error": "Missing or invalid id_ in message"}))
            continue
        function = checkDataType(id_)
        if not function:
            await websocket.send(json.dumps({"error": f"Unknown message type for id_: {id_}", "id_": id_}))
            continue
        data.pop("id_") # separate
        result = await function(id_, **data)
        if result is not None:
            await websocket.send(json.dumps({**result, "id_": id_}))

def checkDataType(id_):
    filtered = re.sub(r'\d', '', id_)
    print(filtered)
    if filtered == '' or filtered not in funcs:
        return False
    else:
        return funcs[filtered]

async def main():
    async with serve(recieve, "127.0.0.1", 6767) as server:
        print("Serving on", server.sockets[0].getsockname())
        await server.serve_forever()

def decoder(text):
    directory = '/home/matteo/scratchFiles/'
    with open(directory + text,"r") as f:
        b64_content = f.read().strip()

    decoded_bytes = base64.b64decode(b64_content)
    decoded_str = decoded_bytes.decode("utf-8")

    data = json.loads(decoded_str)

    print(data)

    with open(directory + "output.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
