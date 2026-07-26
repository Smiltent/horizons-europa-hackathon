
import { Router, type Request, type Response } from "express"
import { createIdGenerator } from "@/utils/id.ts"
import { ws } from "@/src/ws.ts"

const router = Router()
const fetchId = createIdGenerator("GPL")
const createId = createIdGenerator("RC")
const getDataId = createIdGenerator("RGD")

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
    } catch { }

    res.redirect("/projects")
})

router.get("/:id", async (req: Request, res: Response) => {
    const token = (req as unknown as { cookies: Cookies }).cookies?.token
    const id_ = getDataId()

    try {
        const result = await ws.request<{ success: boolean; project?: Project }>(id_, JSON.stringify({
            projectId: req.params.id,
            token,
        }))

        if (!result.success || !result.project) {
            return res.status(404).render("404")
        }

        res.render("projects/view", { proj: result.project })
    } catch {
        res.status(404).render("404")
    }
})

export default router
