
import rootMiddleware from "@/middlewares/root.middleware.ts"
import expressLayouts from "express-ejs-layouts"
import rootRoute from "@/routes/root.routes.ts"
import express from "express"
import path from "path"

export default class Express {
    private app: express.Express

    constructor(private port: string | number = 3000) {
        this.app = express()
        this.i()
    }

    private async i() {
        await this.middleware()
        await this.public()
        await this.routes()
        this.start()
    }

    private async middleware() {
        this.app.use(expressLayouts)
        this.app.use(express.json())
        this.app.use(express.urlencoded({ extended: true }))

        this.app.set("view engine", "ejs")
        this.app.set("layout", "partials/$layout")

        this.app.locals.dev = process.env.NODE_ENV === "dev" ? true : false

        this.app.use(rootMiddleware)
    }

    private async routes() {
        this.app.use("/", rootRoute)

        this.app.use((_req: express.Request, res: express.Response) => {
            res.status(404).render("404")
        })
    }

    private async public() {
        const isDev = process.env.NODE_DEV === "dev"
        this.app.use(
            '/public',
            express.static(path.join(import.meta.dirname as string, '..', 'public'), {
                etag: !isDev,
                lastModified: !isDev,
                maxAge: isDev ? 0 : '10s',
            })
        )
    }

    private async start() {
        this.app.listen(this.port, () => {
            console.info(`Server starting on http://0.0.0.0:${this.port}`)
        })
    }
}