import asyncio
import time
import discord
from fastapi import Request
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
    

async def send_temp_message(interaction: discord.Interaction, content: str, delete_after: float = 5.0):
    """Send a temporary message that will be deleted after specified seconds"""
    message = await interaction.followup.send(content=content, wait=True, ephemeral=False)
    await asyncio.sleep(delete_after)
    try:
        await message.delete()
    except discord.NotFound:
        pass  # Message already deleted


async def log_request_time_async(request: Request, call_next):
	start_time = time.time()
	response = await call_next(request)
	end_time = time.time()

	elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds

	logger.info(f"{request.method} {request.url.path} - elapsed: {elapsed_time:.2f} ms | headers: {request.headers}")

	return response
