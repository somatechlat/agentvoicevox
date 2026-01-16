
import os
import sys
import asyncio
import django

# Setup Django environment
sys.path.append('/Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/ovos-voice-agent/AgentVoiceBoxEngine/backend')
# Force testing settings to avoid env var override
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.testing'
django.setup()

from apps.mcp.tools import list_voices, generate_speech
from apps.voice.models import VoiceModel

async def verify_mcp():
    print("--- Verifying MCP Tools on Real Infrastructure ---")
    
    # 1. Verify list_voices (Database Access)
    print("\n[Action] Listing voices via MCP tool...")
    voices = await list_voices()
    print(f"[Result] Found {len(voices)} voices.")
    for v in voices[:3]:
        print(f" - {v['name']} ({v['provider']})")
        
    if not voices:
        print("[Setup] Database might be empty. creating a test voice...")
        from asgiref.sync import sync_to_async
        await sync_to_async(VoiceModel.objects.create)(
            id="test-voice", name="Test Voice", provider="kokoro", language="en-us"
        )
        voices = await list_voices()
        print(f"[Result] Found {len(voices)} voices after seeding.")

    # 2. Verify generate_speech (Logic & Dependency Check)
    print("\n[Action] Generating speech via MCP tool...")
    try:
        # We use a short text to avoid long processing
        audio = await generate_speech(text="Hello from Real Infrastructure", voice_id="af_heart")
        print(f"[Result] success! Generated {len(audio)} bytes of base64 audio.")
    except Exception as e:
        print(f"[Result] Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_mcp())
