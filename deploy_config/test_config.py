import os
from dotenv import load_dotenv

from discord_bot_libs.constants import DiscordIinfo

load_dotenv()

BOT_KEY = os.getenv('BOT_KEY')

SERVER_ID = DiscordIinfo.SERVER_ID