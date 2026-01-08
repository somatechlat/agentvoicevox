"""
Conversation persistence helpers for realtime sessions.
"""

from __future__ import annotations

from asgiref.sync import sync_to_async

from apps.realtime.models import Conversation, ConversationItem, RealtimeSession


@sync_to_async
def get_or_create_conversation(session_id: str) -> tuple[RealtimeSession, Conversation]:
    """Load or create a conversation for a session."""
    session = RealtimeSession.objects.get(id=session_id)
    conversation = Conversation.objects.filter(session=session).first()
    if conversation:
        return session, conversation
    conversation = Conversation.objects.create(session=session)
    return session, conversation


@sync_to_async
def _next_position(conversation: Conversation) -> int:
    """
    Determines the next available position for a new `ConversationItem`
    within the given conversation.

    Args:
        conversation: The `Conversation` instance to check.

    Returns:
        int: The next available integer position, starting from 0.
    """
    last_item = (
        ConversationItem.objects.filter(conversation=conversation)
        .order_by("-position")
        .first()
    )
    if not last_item:
        return 0
    return last_item.position + 1


async def add_message_item(
    conversation: Conversation,
    role: str,
    content: list[dict],
    status: str = ConversationItem.ItemStatus.COMPLETED,
) -> ConversationItem:
    """Add a message item to a conversation."""
    position = await _next_position(conversation)
    return await sync_to_async(ConversationItem.objects.create)(
        conversation=conversation,
        type=ConversationItem.ItemType.MESSAGE,
        role=role,
        content=content,
        status=status,
        position=position,
    )


async def add_function_call_item(
    conversation: Conversation,
    name: str,
    call_id: str,
    arguments: str,
    status: str = ConversationItem.ItemStatus.COMPLETED,
) -> ConversationItem:
    """Add a function call item to a conversation."""
    position = await _next_position(conversation)
    return await sync_to_async(ConversationItem.objects.create)(
        conversation=conversation,
        type=ConversationItem.ItemType.FUNCTION_CALL,
        name=name,
        call_id=call_id,
        arguments=arguments,
        status=status,
        position=position,
    )


async def add_function_call_output_item(
    conversation: Conversation,
    call_id: str,
    output: str,
    status: str = ConversationItem.ItemStatus.COMPLETED,
) -> ConversationItem:
    """Add a function call output item to a conversation."""
    position = await _next_position(conversation)
    return await sync_to_async(ConversationItem.objects.create)(
        conversation=conversation,
        type=ConversationItem.ItemType.FUNCTION_CALL_OUTPUT,
        call_id=call_id,
        output=output,
        status=status,
        position=position,
    )


@sync_to_async
def clear_conversation_items(conversation: Conversation) -> None:
    """Delete conversation items for a conversation."""
    ConversationItem.objects.filter(conversation=conversation).delete()
