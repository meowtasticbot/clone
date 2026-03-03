from typing import Dict, Optional

from pyrogram import Client

from config import API_HASH, API_ID
from Clonify.utils.database import clonebotdb, get_assistant

_clone_assistants: Dict[int, Client] = {}


def _session_name(bot_id: int) -> str:
    return f"clone_assistant_{bot_id}"


async def _build_client_from_string(bot_id: int, session_string: str) -> Client:
    client = Client(
        name=_session_name(bot_id),
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
    )
    await client.start()
    me = await client.get_me()
    client.id = me.id
    client.name = me.mention
    client.username = me.username
    return client


async def set_clone_string(bot_id: int, session_string: str) -> Client:
    # Build/validate new assistant first so old assistant is not lost on invalid strings.
    client = await _build_client_from_string(bot_id, session_string)

    old_client = _clone_assistants.pop(bot_id, None)
    if old_client:
        try:
            await old_client.stop()
        except Exception:
            pass

    clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"assistant_string": session_string}},
        upsert=True,
    )
    _clone_assistants[bot_id] = client
    return client


async def disconnect_clone_assistant(bot_id: int):
    client = _clone_assistants.pop(bot_id, None)
    if client:
        try:
            await client.stop()
        except Exception:
            pass
    clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$unset": {"assistant_string": ""}},
        upsert=True,
    )


async def get_clone_assistant(client: Client, chat_id: int):
    bot = await client.get_me()
    bot_id = bot.id

    custom = _clone_assistants.get(bot_id)
    if custom:
        return custom

    data = clonebotdb.find_one({"bot_id": bot_id}) or {}
    session_string: Optional[str] = data.get("assistant_string")
    if session_string:
        try:
            custom = await _build_client_from_string(bot_id, session_string)
            _clone_assistants[bot_id] = custom
            return custom
        except Exception:
            # Don't auto-remove configured string on transient errors.
            # If owner wants fallback they can use /disconnect explicitly.
            pass

    return await get_assistant(chat_id)
