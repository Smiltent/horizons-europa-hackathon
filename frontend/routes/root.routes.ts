
import { Router, type Request, type Response } from "express"
import { createIdGenerator } from "@/utils/id.ts"
import { ws } from "@/src/ws.ts"

const router = Router()
const loginId = createIdGenerator("L")
const logoutId = createIdGenerator("LO")

router.get("/", (_req: Request, res: Response) => {
    res.render("lander")
})

router.get("/login", (_req: Request, res: Response) => {
    res.render("login", { error: null })
})

router.post("/login", async (req: Request, res: Response) => {
    const { username, password } = req.body as { username: string; password: string }

    const id_ = loginId()

    try {
        const result = await ws.request<{ success: boolean; token?: string }>(id_, JSON.stringify({
            username,
            password,
        }))

        if (result.success && result.token) {
            res.cookie("token", result.token, { httpOnly: true, sameSite: "lax" })
            return res.redirect("/")
        }

        res.render("login", { error: "Invalid credentials" })
    } catch {
        res.render("login", { error: "Could not reach auth server" })
    }
})

async function performLogout(req: Request, res: Response) {
    const token = (req as unknown as { cookies: Record<string, string> }).cookies?.token

    if (token) {
        const id_ = logoutId()
        try {
            await ws.request(id_, JSON.stringify({ token }))
        } catch (err) {
            console.debug(`WS request failed: ${err}`)
        }
    }

    res.clearCookie("token")
    res.redirect("/login")
}

router.get("/logout", performLogout)
router.post("/logout", performLogout)

export default router
