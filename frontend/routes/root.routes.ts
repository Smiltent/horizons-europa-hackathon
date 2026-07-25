
import { Router, type Request, type Response } from "express"
import { createIdGenerator } from "@/utils/id.ts"
import { ws } from "@/src/ws.ts"

const router = Router()

const loginId = createIdGenerator("L")

router.get("/", (_req: Request, res: Response) => {
    res.render("lander")
})

router.get("/login", (_req: Request, res: Response) => {
    res.render("login", { error: null })
})

router.post("/login", async (req: Request, res: Response) => {
    const { Username: username, password } = req.body as { Username: string; password: string }

    const id = loginId()

    try {
        const result = await ws.request<{ success: boolean; token?: string }>(id, {
            username,
            password,
        })

        if (result.success && result.token) {
            res.cookie("token", result.token, { httpOnly: true, sameSite: "lax" })
            return res.redirect("/")
        }

        res.render("login", { error: "Invalid credentials" })
    } catch {
        res.render("login", { error: "Could not reach auth server" })
    }
})

export default router
