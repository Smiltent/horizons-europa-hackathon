
import Express from "@/src/Express.ts"
import { ws } from "@/src/ws.ts"

new Express(process.env.PORT)

ws.onOpen(() => {
    ws.send(JSON.stringify({
        id: "L00000000001",
        username: "smil",
        password: "Tagung+2"
    }))
})

ws.onMessage((data) => {
    console.info("[WS] Received:", data)
})
