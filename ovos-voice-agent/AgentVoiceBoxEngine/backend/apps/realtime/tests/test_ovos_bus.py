import pytest
from unittest.mock import MagicMock, patch
from apps.realtime.ovos_bus import OVOSIntelligenceBridge
from ovos_bus_client import Message

@pytest.fixture
def bridge():
    return OVOSIntelligenceBridge()

def test_register_session(bridge):
    callback = MagicMock()
    bridge.register_session("session_123", callback)
    assert "session_123" in bridge._session_callbacks
    assert bridge._session_callbacks["session_123"] == callback

def test_unregister_session(bridge):
    callback = MagicMock()
    bridge.register_session("session_123", callback)
    bridge.unregister_session("session_123")
    assert "session_123" not in bridge._session_callbacks

@patch("apps.realtime.ovos_bus.MessageBusClient")
@pytest.mark.asyncio
async def test_send_utterance(mock_bus_client, bridge):
    mock_instance = mock_bus_client.return_value
    bridge.client = mock_instance
    
    await bridge.send_utterance("session_1", "hello world")
    
    # Check if emit was called with correct message
    args, kwargs = mock_instance.emit.call_args
    message = args[0]
    assert message.msg_type == "recognizer_loop:utterance"
    assert message.data["utterances"] == ["hello world"]
    assert message.context["session_id"] == "session_1"

@pytest.mark.asyncio
async def test_handle_speak(bridge):
    callback = MagicMock()
    bridge.register_session("session_1", callback)
    
    # Mock the loop to avoid "Event loop is closed" error
    mock_loop = MagicMock()
    bridge._loop = mock_loop
    
    message = Message(
        "speak",
        data={"utterance": "how can I help?"},
        context={"session_id": "session_1"}
    )
    
    bridge._handle_speak(message)
    
    # Callback should be scheduled on the loop
    mock_loop.call_soon_threadsafe.assert_called_once_with(callback, "how can I help?", message.context)
