import base64
import json
import asyncio
import re
import aiohttp
from websockets.asyncio.server import serve
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.environ.get("HOST", "100.65.0.67")
PORT = int(os.environ.get("PORT", 6767))

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

            try:
                session_cookie = resp.cookies.get("scratchsessionsid")
            except Exception as e:
                print(e)

    print(id_, username, password)
    idList = "dataBase/ids.json"

    if os.path.exists(idList):
        with open(idList, "r") as f:
            data = json.load(f)
    else:
        data = {}

    key = re.sub(r'\d', '', id_)
    identif = re.sub(r'\D', '', id_)
    data[key] = identif  # updates existing key or adds it if new

    with open(idList, "w") as file:
        json.dump(data, file, indent=2)
    savedir = "dataBase/userData/"

    data = {
        "username": username,
        "password": password,
        "session_id": session_cookie.value if session_cookie else None,
        "token": result.get("token"),
    }

    with open(savedir + username +".json", "w") as file:
        json.dump(data, file, indent=2)

    return {
        "success": True,
        "username": username,
        "session_id": session_cookie.value if session_cookie else None,
        "token": result.get("token"),
    }

async def repoCreate(id_, **kwargs):
    pass  # TODO

async def repoCreateOK(id_, **kwargs):
    pass  # TODO

async def repoDelete(id_, **kwargs):
    pass  # TODO

async def repoDeleteOK(id_, **kwargs):
    pass  # TODO

async def repoCommit(id_, **kwargs):
    pass  # TODO

async def repoCommitOK(id_, **kwargs):
    pass  # TODO

async def repoGetData(id_, **kwargs):
    pass  # TODO

async def repoGetDataResponse(id_, **kwargs):
    pass  # TODO

async def getRepoList(id_, **kwargs):
    pass  # TODO

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
        while True:
            try:
                data = json.loads(message)
                print(message)
                if data:
                    break
            except Exception as e:
                e = str(e)
                await websocket.send(e)

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
        while True:
            try:
                result = await function(id_, **data)
                if result:
                    break
            except Exception as e:
                e = str(e)
                await websocket.send(e)

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
    async with serve(recieve, HOST, PORT) as server:
        print("Serving on", server.sockets[0].getsockname())
        await server.serve_forever()

def decoder(text):
    directory = 'dataBase/'
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
