
from discord.ext import commands
from loguru import logger

from discord_bot_libs.manager import bot_manager


def setup(bot: commands.Bot):
    logger.info(f"Setting up welcome bot")
    routes = [on_message]
    for route in routes:
        bot.add_listener(route)


async def on_message(message):
    await bot_manager.on_message(message)



    