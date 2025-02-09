import asyncio
import discord
from loguru import logger
import yt_dlp
from discord_bot_api.model.music_model import MusicInfo, map_music_info


async def get_music_info(query) -> MusicInfo:
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            music_info = map_music_info(info)
            return music_info
    except Exception as e:
        logger.error(f"Failed to get music info: {e}")
        return None
    

async def send_temp_message(interaction: discord.Interaction, content: str, delete_after: float = 10.0):
    """Send a temporary message that will be deleted after specified seconds"""
    message = await interaction.followup.send(content=content, wait=True, ephemeral=False)
    await asyncio.sleep(delete_after)
    try:
        await message.delete()
    except discord.NotFound:
        pass  # Message already deleted
