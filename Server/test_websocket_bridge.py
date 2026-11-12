"""Offline integration test: real WebSocket bridge and mock TCP backend; no AI or DB calls."""
import asyncio
import json
import unittest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from WebSocketBridge import relay

class BridgeTests(unittest.IsolatedAsyncioTestCase):
    async def test_handshake_framing_and_conversation(self):
        seen = []
        async def backend(reader, writer):
            writer.write(b'{"Response Code":"200","MESSAGE":{"HANDSHAKE":"True"}}\n')
            await writer.drain()
            seen.append(json.loads(await reader.readline()))
            for reply in [
                {"CONVOID":7,"RESUMED":False,"MESSAGES":[{"role":"assistant","content":"What does your loop do?"}]},
                {"CONVOID":7,"REPLY":"Look at the stopping condition."},
            ]:
                seen.append(json.loads(await reader.readline()))
                encoded = json.dumps({"Response Code":"200","MESSAGE":reply}).encode()+b'\n'
                # Deliberately split a response across writes.
                writer.write(encoded[:12]); await writer.drain(); await asyncio.sleep(0)
                writer.write(encoded[12:]); await writer.drain()
            writer.close(); await writer.wait_closed()
        tcp = await asyncio.start_server(backend, '127.0.0.1', 0)
        port = tcp.sockets[0].getsockname()[1]
        async def handler(ws):
            await relay(ws, port=port)
        async with tcp, serve(handler, '127.0.0.1', 0) as bridge:
            wsport = bridge.sockets[0].getsockname()[1]
            async with connect(f'ws://127.0.0.1:{wsport}') as ws:
                await ws.send(json.dumps({"MESSAGE":{"METHOD":"GET","INFO":"userInfo"}}))
                self.assertEqual(json.loads(await ws.recv())["Response Code"], '400')
                await ws.send(json.dumps({"MESSAGE":{"METHOD":"POST","INFO":"startAIConversation","PARAMS":{"USERID":1,"SUBMISSIONID":7}}}))
                self.assertEqual(json.loads(await ws.recv())["MESSAGE"]["CONVOID"], 7)
                await ws.send(json.dumps({"MESSAGE":{"METHOD":"POST","INFO":"sendAIMessage","PARAMS":{"USERID":1,"CONVOID":7,"TEXT":"Help"}}}))
                self.assertEqual(json.loads(await ws.recv())["MESSAGE"]["REPLY"], "Look at the stopping condition.")
        self.assertEqual(seen[0]["MESSAGE"]["METHOD"], "HANDSHAKE")
        self.assertEqual(seen[1]["MESSAGE"]["INFO"], "startAIConversation")
        self.assertEqual(seen[2]["MESSAGE"]["PARAMS"]["TEXT"], "Help")

if __name__ == '__main__':
    unittest.main()
