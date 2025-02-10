import traceback

from config import *
from discord_bot_api.bot_client import client
import api





if __name__ == "__main__":
    # api.keep_alive()
    try:
        client.run(BOT_KEY)
    except Exception as e:
        logger.error(f"Failed to run bot: {e} | Traceback: \n{traceback.format_exc()}")