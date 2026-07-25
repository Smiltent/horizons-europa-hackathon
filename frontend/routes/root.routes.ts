

import { Router, type Request, type Response } from "express"
const router = Router()

router.get("/", (_req: Request, res: Response) => {
    res.render("lander")
})

export default router