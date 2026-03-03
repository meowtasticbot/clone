from typing import Dict

from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Message

from config import API_HASH, API_ID, OWNER_ID, SUPPORT_CHAT
from Clonify.utils.database.clonedb import get_owner_id_from_db
from Clonify.utils.clone_assistant import disconnect_clone_assistant, set_clone_string

connect_states: Dict[int, dict] = {}


def _is_owner(user_id: int, bot_id: int) -> bool:
    c_owner = get_owner_id_from_db(bot_id)
    return user_id in [OWNER_ID, c_owner]


@Client.on_message(filters.command(["setstring", "setdtring"]))
async def setstring_cmd(client: Client, message: Message):
    bot = await client.get_me()
    if not message.from_user or not _is_owner(message.from_user.id, bot.id):
        return await message.reply_text(f"Only clone owner can use this command. Join {SUPPORT_CHAT}")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /setstring <pyrogram_string_session>")

    session_string = message.text.split(None, 1)[1].strip()
    try:
        assistant = await set_clone_string(bot.id, session_string)
        await message.reply_text(
            f"✅ Assistant connected: {assistant.name}\nNow music will play with this string account."
        )
    except Exception as e:
        await message.reply_text(f"❌ Invalid string/session failed: {type(e).__name__}: {e}")


@Client.on_message(filters.command("disconnect"))
async def disconnect_cmd(client: Client, message: Message):
    bot = await client.get_me()
    if not message.from_user or not _is_owner(message.from_user.id, bot.id):
        return await message.reply_text(f"Only clone owner can use this command. Join {SUPPORT_CHAT}")

    await disconnect_clone_assistant(bot.id)
    connect_states.pop(message.from_user.id, None)
    await message.reply_text(
        "✅ Custom assistant disconnected.\nNow bot will use normal default assistant for music."
    )


@Client.on_message(filters.command("connect"))
async def connect_cmd(client: Client, message: Message):
    bot = await client.get_me()
    if not message.from_user or not _is_owner(message.from_user.id, bot.id):
        return await message.reply_text(f"Only clone owner can use this command. Join {SUPPORT_CHAT}")

    connect_states[message.from_user.id] = {"step": "phone", "bot_id": bot.id}
    await message.reply_text(
        "Send phone number with country code.\nExample: +919876543210\n\nUse /disconnect to cancel."
    )


@Client.on_message(filters.private & filters.text & ~filters.command(["connect", "disconnect", "setstring", "setdtring"]))
async def connect_flow(client: Client, message: Message):
    if not message.from_user:
        return

    state = connect_states.get(message.from_user.id)
    if not state:
        return

    bot = await client.get_me()
    if state.get("bot_id") != bot.id:
        return
    if not _is_owner(message.from_user.id, bot.id):
        connect_states.pop(message.from_user.id, None)
        return

    step = state.get("step")

    if step == "phone":
        phone = message.text.strip()
        login_client = Client(
            name=f"tmp_connect_{message.from_user.id}_{bot.id}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True,
        )
        await login_client.connect()
        try:
            sent = await login_client.send_code(phone)
        except Exception as e:
            await login_client.disconnect()
            connect_states.pop(message.from_user.id, None)
            return await message.reply_text(f"Failed to send OTP: {type(e).__name__}: {e}")

        state.update(
            {
                "step": "otp",
                "phone": phone,
                "phone_code_hash": sent.phone_code_hash,
                "login_client": login_client,
            }
        )
        return await message.reply_text("OTP sent. अब OTP bhejo (digits only).")

    if step == "otp":
        otp = message.text.strip().replace(" ", "")
        login_client = state["login_client"]
        try:
            await login_client.sign_in(
                phone_number=state["phone"],
                phone_code_hash=state["phone_code_hash"],
                phone_code=otp,
            )
        except SessionPasswordNeeded:
            state["step"] = "password"
            return await message.reply_text("2FA password bhejo.")
        except Exception as e:
            await login_client.disconnect()
            connect_states.pop(message.from_user.id, None)
            return await message.reply_text(f"OTP verify failed: {type(e).__name__}: {e}")

        session_string = await login_client.export_session_string()
        await login_client.disconnect()
        connect_states.pop(message.from_user.id, None)
        try:
            assistant = await set_clone_string(bot.id, session_string)
            return await message.reply_text(
                f"✅ Connected successfully: {assistant.name}\nNow this account will be used for music."
            )
        except Exception as e:
            return await message.reply_text(f"Connected but save/start failed: {type(e).__name__}: {e}")

    if step == "password":
        password = message.text.strip()
        login_client = state["login_client"]
        try:
            await login_client.check_password(password=password)
        except Exception as e:
            await login_client.disconnect()
            connect_states.pop(message.from_user.id, None)
            return await message.reply_text(f"Password failed: {type(e).__name__}: {e}")

        session_string = await login_client.export_session_string()
        await login_client.disconnect()
        connect_states.pop(message.from_user.id, None)

        try:
            assistant = await set_clone_string(bot.id, session_string)
            return await message.reply_text(
                f"✅ Connected successfully: {assistant.name}\nNow this account will be used for music."
            )
        except Exception as e:
            return await message.reply_text(f"Connected but save/start failed: {type(e).__name__}: {e}")
