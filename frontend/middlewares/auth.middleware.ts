
import type { NextFunction, Request, Response } from "express"

const PUBLIC = ["/login"]

export default function authMiddleware(req: Request, res: Response, next: NextFunction) {
    if (process.env.NODE_DEV === "design") return next() 

    if (PUBLIC.some((p) => req.path.startsWith(p))) return next()
    if (!(req as unknown as { cookies: Record<string, string> }).cookies?.token) {
        return res.redirect("/")
    }
    next()
}
