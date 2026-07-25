
import type { NextFunction, Request, Response } from "express"
import getRealIP from "@/utils/ip.ts"

export default function root(req: Request, res: Response, next: NextFunction) {
    const ip = getRealIP(req)
    res.on("finish", () => {
        console.debug(`${ip} | ${req.method} ${res.statusCode} ${req.originalUrl}`)
    })

    next()
}