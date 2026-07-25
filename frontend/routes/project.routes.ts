
import { Router, type Request, type Response } from "express"
import { createIdGenerator } from "@/utils/id.ts"
import { ws } from "@/src/ws.ts"

const router = Router()
const fetchId = createIdGenerator("GRL")
const createId = createIdGenerator("RC")

type Project = {
    id: string
    name: string
    created: boolean
    isPublished?: boolean
    dateOfCreation?: string
}

type Cookies = Record<string, string>

router.get("/", async (req: Request, res: Response) => {
    const token = (req as unknown as { cookies: Cookies }).cookies?.token
    const id_ = fetchId()

    try {
        const result = await ws.request<{ projects: Project[] }>(id_, JSON.stringify({
            token,
        }))

        const created = result.projects.filter((p) => p.created)
        const nonCreated = result.projects.filter((p) => !p.created)

        res.render("projects/list", { created, nonCreated, error: null })
    } catch {
        res.render("projects/list", { created: [], nonCreated: [], error: "Could not load projects" })
    }
})

router.post("/:projectId/create", async (req: Request, res: Response) => {
    const token = (req as unknown as { cookies: Cookies }).cookies?.token
    const id_ = createId()

    try {
        await ws.request(id_, JSON.stringify({
            projectId: req.params.projectId,
            token,
        }))
    } catch { /* redirect regardless */ }

    res.redirect("/projects")
})

router.get("/:id", async (_req: Request, _res: Response) => {
    // TODO: single project view
})

export default router
