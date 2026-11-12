"""Local development bridge: browser WebSocket -> existing newline-framed TCP server.

Not a public deployment gateway: the existing TCP server trusts client USERID.
"""
import asyncio
import json
import os
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

MAX_MESSAGE = 32_000

async def relay(websocket, host="127.0.0.1", port=8342):
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port, limit=2_000_000), 10)
        handshake = json.loads(await asyncio.wait_for(reader.readline(), 10))
        if handshake.get("MESSAGE", {}).get("HANDSHAKE") != "True":
            raise ValueError("Unexpected TCP handshake")
        writer.write(b'{"MESSAGE":{"METHOD":"HANDSHAKE","INFO":"ACK"}}\n')
        await writer.drain()
        async for raw in websocket:
            try:
                request = json.loads(raw)
                msg = request.get("MESSAGE") if isinstance(request, dict) else None
                # Only expose the two conversation operations in this local bridge.
                if not isinstance(msg, dict) or msg.get("METHOD") != "POST" or msg.get("INFO") not in {"startAIConversation", "sendAIMessage"}:
                    raise ValueError("Only AI conversation requests are supported")
            except (ValueError, TypeError) as exc:
                await websocket.send(json.dumps({"Response Code":"400", "MESSAGE":{"ERROR":str(exc)}}))
                continue
            writer.write(json.dumps(request).encode("utf-8") + b"\n")
            await writer.drain()
            response = await asyncio.wait_for(reader.readline(), 85)
            if not response:
                raise ConnectionError("TCP server disconnected")
            await websocket.send(json.dumps(json.loads(response)))
    except ConnectionClosed:
        pass
    except Exception:
        try:
            await websocket.send(json.dumps({"Response Code":"502", "MESSAGE":{"ERROR":"Backend unavailable or timed out. Check SocketServer.py, then reload the portal."}}))
            await websocket.close(code=1011, reason="Backend unavailable")
        except ConnectionClosed:
            pass
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()

async def main():
    origins = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    print("Local WebSocket bridge: ws://127.0.0.1:8343 -> TCP 127.0.0.1:8342")
    async with serve(relay, "127.0.0.1", 8343, origins=[o.strip() for o in origins], max_size=MAX_MESSAGE):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
