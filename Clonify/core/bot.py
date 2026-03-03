from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config

from ..logging import LOGGER


class PRO(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")
        super().__init__(
            name="Clonify",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            max_concurrent_transmissions=7,
        )
 
    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        logger_id = config.LOGGER_ID
        if str(logger_id).strip() == "-100":
            LOGGER(__name__).warning(
                "LOGGER_ID is set to -100 (placeholder). Skipping startup log checks."
            )
            LOGGER(__name__).info(f"Music Bot Started as {self.name}")
            return

        try:
            await self.send_message(
                chat_id=logger_id,
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b><u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).warning(
                "Bot can't access LOGGER_ID. Add the bot to your log group/channel or fix LOGGER_ID. Starting without startup log checks."
            )
            LOGGER(__name__).info(f"Music Bot Started as {self.name}")
            return
        except ValueError:
            LOGGER(__name__).warning(
                "LOGGER_ID is invalid. Use a proper channel/group ID (e.g. -100xxxxxxxxxx) or username. Starting without startup log checks."
            )
            LOGGER(__name__).info(f"Music Bot Started as {self.name}")
            return
        except Exception as ex:
            LOGGER(__name__).warning(
                f"Bot failed to access LOGGER_ID ({type(ex).__name__}). Starting without startup log checks."
            )
            LOGGER(__name__).info(f"Music Bot Started as {self.name}")
            return

        try:
            a = await self.get_chat_member(logger_id, self.id)
            if a.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).warning(
                    "Bot is not admin in LOGGER_ID. Promote it if you want logging features to work fully."
                )
        except Exception as ex:
            LOGGER(__name__).warning(
                f"Skipping LOGGER_ID admin check due to {type(ex).__name__}."
            )
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
