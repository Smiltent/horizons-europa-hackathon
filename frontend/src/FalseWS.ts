
type MessageHandler = (data: string | ArrayBuffer) => void

// Mirrors the raw shape Scratch's own API returns from
// api.scratch.mit.edu/users/:username/projects — this is what getProjectList
// (id prefix "GPL") forwards as-is on the real backend.
type ScratchProject = {
    id: number
    title: string
    is_published?: boolean
    history?: { created?: string }
}

const FAKE_PROJECTS: ScratchProject[] = [
    { id: 100000001, title: "Design Mode Project A", is_published: true, history: { created: "2026-06-01" } },
    { id: 100000002, title: "Design Mode Project B", is_published: false, history: { created: "2026-06-15" } },
    { id: 100000004, title: "Design Mode Project c", is_published: false, history: { created: "2026-06-15" } },
    { id: 100000005, title: "Design Mode Project d", is_published: false, history: { created: "2026-06-15" } },
    { id: 100000003, title: "Unlinked Scratch Project", is_published: false, history: { created: "2026-06-20" } },
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
            case "GPL":
                return { success: true, username: payload.username, projects: FAKE_PROJECTS }
            case "RC":
                return { success: true, projectId: payload.projectId }
            case "RCOK":
            case "RD":
            case "RDOK":
            case "RCM":
            case "RCMOK":
                return { success: true }
            case "RGD": {
                const project = FAKE_PROJECTS.find((p) => p.id === payload.projectId)
                return project
                    ? { success: true, project }
                    : { success: false, error: "not_found" }
            }
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
