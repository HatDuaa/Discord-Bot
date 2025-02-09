

import asyncio
import discord
from loguru import logger
from pydub import AudioSegment
from pydub.playback import play


async def on_message(message):
    logger.info(f"Message received: {message.content}")
    if message.content == 'hello':
        await message.channel.send("Hello! I am a Hạt_Bí's bot.")


async def on_reaction_add(reaction, user):
    logger.info(f"Reaction added: {reaction.emoji} by {user.name}")

