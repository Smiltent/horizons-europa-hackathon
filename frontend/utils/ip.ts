
import type { Request } from "express"

export default function getRealIP(req: Request) {
    if (req.headers["cf-connecting-ip"]) return req.headers["cf-connecting-ip"] // cloudflare
    if (req.headers["x-real-ip"]) return req.headers["x-real-ip"]

    return req.ip
}