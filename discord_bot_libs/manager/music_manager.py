import yt_dlp as youtube_dl
import discord
import asyncio
from loguru import logger
from datetime import datetime, timedelta

from discord_bot_api.model.music_model import MusicInfo, MusicState
from discord_bot_libs.ui.music_ui import MusicControlButtons, create_now_playing_embed
from discord_bot_libs.utils import get_music_info, send_temp_message


music_state = MusicState()


async def play(interaction: discord.Interaction, query):
    music_info = await get_music_info(query)
    if not music_info:
        logger.error(f"❌ Music not found for query: {query}")
        await send_temp_message(interaction, "❌ Không tìm thấy bài hát")
        return
    
    music_state.add_to_queue(music_info)
    queue_length = len(music_state.get_queue())
    await send_temp_message(interaction, f"➕ Đã thêm vào hàng đợi: {music_info}")

    if not music_state.is_playing:
        logger.info(f"🎵 Start music")
        await play_loop(interaction)
    else:
        logger.info(f"➕ Added to queue: {music_info} | Queue length: {queue_length}")

async def play_loop(interaction: discord.Interaction):
    while music_state.get_queue():
        music_info = music_state.remove_from_queue()
        if music_info:
            now = datetime.now()
            logger.info(f"🎵 Playing music: {music_info}")
            music_state.is_playing = True
            await play_music(interaction, music_info)
            if music_state.get_queue():
                logger.info(f"Playing next music in 1 seconds")
                await asyncio.sleep(1)
    music_state.is_playing = False


async def play_music(interaction: discord.Interaction, music_info: MusicInfo):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await send_temp_message(interaction, "❌ Bạn cần vào kênh thoại trước")
        return

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    embed = create_now_playing_embed(music_info)
    view = MusicControlButtons(voice_client)
    
    if music_state.current_message:
        await music_state.current_message.edit(embed=embed, view=view)
    else:
        message = await interaction.followup.send(embed=embed, view=view)
        music_state.current_message = message

    def after_playing(error):
        if error:
            logger.error(f"Error playing audio: {error}")
        logger.info(f"🎵 Finished playing: {music_info}")

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    # Tạo audio source với các tùy chọn FFMPEG
    audio_source = discord.FFmpegPCMAudio(
        music_info.url,
        before_options=FFMPEG_OPTIONS['before_options'],
        options=FFMPEG_OPTIONS['options']
    )
    
    # Phát nhạc với audio source đã được cấu hình
    voice_client.play(audio_source, after=after_playing)

    # Đợi cho đến khi bài hát thực sự kết thúc
    while voice_client and voice_client.is_playing():
        try:
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error while playing: {e}")
            break



    
    



