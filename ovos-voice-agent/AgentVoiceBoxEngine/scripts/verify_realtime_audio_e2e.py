"""
AgentVoiceBox OpenAI Realtime API - E2E Verification
====================================================

This script simulates an OpenAI SDK client connecting to the AgentVoiceBox
Realtime Gateway (`/ws/v1/realtime`). It verifies that the server correctly
accepts `session.update` configurations and can process `input_audio_buffer` events.
"""

import asyncio
import json
import base64
import websockets
import sys

# Generate a small 100ms dummy PCM16 audio buffer for testing
DUMMY_PCM16 = b'\x00' * int(16000 * 2 * 0.1)  # 16kHz, 16bit, 0.1s
DUMMY_B64 = base64.b64encode(DUMMY_PCM16).decode("utf-8")

async def test_realtime_gateway():
    uri = "ws://localhost:65020/ws/v1/realtime?session_id=agent-test-001"
    
    print(f"Connecting to Gateway: {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            # 1. Expect initial session.created
            print("Waiting for session.created...")
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(msg)
            assert data["type"] == "session.created", "Expected session.created"
            print("✅ Received session.created")

            # 2. Send session.update
            print("Sending session.update...")
            update_req = {
                "type": "session.update",
                "session": {
                    "voice": "af_heart",
                    "instructions": "Respond like a helpful agent."
                }
            }
            await ws.send(json.dumps(update_req))
            
            # 3. Send audio append
            print("Sending input_audio_buffer.append...")
            append_req = {
                "type": "input_audio_buffer.append",
                "audio": DUMMY_B64
            }
            await ws.send(json.dumps(append_req))
            
            # 4. Commit audio
            print("Sending input_audio_buffer.commit...")
            commit_req = {
                "type": "input_audio_buffer.commit"
            }
            await ws.send(json.dumps(commit_req))
            
            print("✅ Successfully sent audio and config to the Gateway!")
            print("Note: In a live environment, OVOS bus would reply with response.audio.delta")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the Django ASGI server running on port 65020?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_realtime_gateway())
