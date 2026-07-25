
import Express from "@/src/Express.ts"
import { ws } from "@/src/ws.ts"

new Express(process.env.PORT)

ws.onOpen(() => {
    // ws.send(JSON.stringify({
    //     id_: "L00000000001",
    //     username: "Smil",
    //     password: "Smil"
    // }))
})

ws.onMessage((data) => {
    console.info("[WS] Received:", data)
})
