
import ServerWS from "@/src/ServerWS.ts"
import FalseWS from "@/src/FalseWS.ts"

export const ws = process.env.NODE_DEV === "design" ? new FalseWS() : new ServerWS()
