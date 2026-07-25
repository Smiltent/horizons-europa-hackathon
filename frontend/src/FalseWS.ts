
type MessageHandler = (data: string | ArrayBuffer) => void

type Project = {
    id: string
    name: string
    created: boolean
    isPublished?: boolean
    dateOfCreation?: string
}

const FAKE_PROJECTS: Project[] = [
    { id: "100000001", name: "Design Mode Project A", created: true, isPublished: true, dateOfCreation: "2026-06-01" },
    { id: "100000002", name: "Design Mode Project B", created: true, isPublished: false, dateOfCreation: "2026-06-15" },
    { id: "100000003", name: "Unlinked Scratch Project", created: false },
]

export default class FalseWS {
    private handlers: MessageHandler[] = []
    private openHandlers: (() => void)[] = []

    constructor() {
        console.info("[FalseWS] Design mode — using fake data, no real WS connection")
        queueMicrotask(() => {
            for (const handler of this.openHandlers) handler()
        })
    }

    request<T>(id_: string, data: string | Record<string, unknown>, _timeout = 5000): Promise<T> {
        const payload = typeof data === "string" ? JSON.parse(data) as Record<string, unknown> : data
        console.info(`[FalseWS] Fake request for ${id_}:`, payload)
        return Promise.resolve(this.fakeResponse(id_, payload) as T)
    }

    private fakeResponse(id_: string, payload: Record<string, unknown>): Record<string, unknown> {
        const prefix = id_.replace(/\d/g, "")

        switch (prefix) {
            case "L":
                return { success: true, token: "design-mode-token", username: payload.username ?? "designer" }
            case "LO":
                return { success: true }
            case "GRL":
                return { success: true, projects: FAKE_PROJECTS }
            case "RC":
                return { success: true, projectId: payload.projectId }
            case "RCOK":
            case "RD":
            case "RDOK":
            case "RCM":
            case "RCMOK":
                return { success: true }
            case "RGD":
            case "RGDR":
                return { success: true, data: null }
            default:
                return { success: true }
        }
    }

    send(_data: string | ArrayBufferLike | Blob | ArrayBufferView) {
        console.info("[FalseWS] send() ignored in design mode")
    }

    onOpen(handler: () => void) {
        this.openHandlers.push(handler)
    }

    onMessage(handler: MessageHandler) {
        this.handlers.push(handler)
    }

    close() {
        // no-op in design mode
    }
}
