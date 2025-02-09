import discord
from loguru import logger

from config import SERVER_ID




logger.info(f"Bot_client will only work in server with ID: {SERVER_ID}")
GUILD_ID = discord.Object(id=SERVER_ID)

