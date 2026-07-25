
type MessageHandler = (data: string | ArrayBuffer) => void
type PendingResolver = (data: unknown) => void

export default class ServerWS {
    private ws: WebSocket | null = null
    private handlers: MessageHandler[] = []
    private openHandlers: (() => void)[] = []
    private pending = new Map<string, PendingResolver>()
    private reconnectDelay = 3000

    constructor() {
        const target = process.env.SERVER_WS
        if (!target) throw new Error("SERVER_WS env variable is not set")
        this.connect(target)
    }

    private connect(target: string) {
        const url = target.startsWith("ws://") || target.startsWith("wss://")
            ? target
            : `ws://${target}`

        console.info(`Connecting to ${url}`)
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
            console.info("WS Connected")
            for (const handler of this.openHandlers) handler()
        }

        this.ws.onmessage = (event) => {
            let parsed: Record<string, unknown> | null = null
            try { parsed = JSON.parse(event.data) } catch { /* not JSON */ }

            if (parsed?.id && this.pending.has(parsed.id as string)) {
                this.pending.get(parsed.id as string)!(parsed)
                return
            }

            for (const handler of this.handlers) handler(event.data)
        }

        this.ws.onclose = (event) => {
            console.warn(`[WS] Disconnected — code: ${event.code}, clean: ${event.wasClean}, reason: "${event.reason || "none"}", retrying in ${this.reconnectDelay}ms`)
            setTimeout(() => this.connect(target), this.reconnectDelay)
        }

        this.ws.onerror = (event) => {
            console.error("[WS] Error:", (event as ErrorEvent).message ?? event)
        }
    }

    request<T>(id: string, data: string | Record<string, unknown>, timeout = 5000): Promise<T> {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.pending.delete(id)
                reject(new Error("WS request timed out"))
            }, timeout)

            this.pending.set(id, (response) => {
                clearTimeout(timer)
                this.pending.delete(id)
                resolve(response as T)
            })
            
            const payload = typeof data === "string"
                ? JSON.stringify({ id, ...JSON.parse(data) })
                : JSON.stringify({ id, ...data })
            this.send(payload)
        })
    }

    send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn("Cannot send — not connected")
            return
        }

        console.info(`[WS] Sent: ${data}`)
        this.ws.send(data)
    }

    onOpen(handler: () => void) {
        this.openHandlers.push(handler)
    }

    onMessage(handler: MessageHandler) {
        this.handlers.push(handler)
    }

    close() {
        this.ws?.close()
        this.ws = null
    }
}
