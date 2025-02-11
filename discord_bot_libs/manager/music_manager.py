from concurrent.futures import ThreadPoolExecutor
import threading
import time
import discord
import asyncio
from loguru import logger
from typing import Optional

from discord_bot_api.model.music_model import MusicInfo, MusicState, RequestInfo, map_request_info
from discord_bot_libs.ui.music_ui import MusicControlButtons, create_now_playing_embed
from discord_bot_libs.utils import get_music_info, send_temp_message

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class MusicPlayer:
    def __init__(self):
        self.music_state = MusicState()
        self.voice_client: Optional[discord.VoiceClient] = None
        self.last_interaction: Optional[discord.Interaction] = None
        self.player_thread_pool = ThreadPoolExecutor(max_workers=1)
        self.current_player_task = None

    async def play(self, interaction: discord.Interaction, query: str):
        """Handle play command"""
        self.last_interaction = interaction
        music_info = await get_music_info(query)
        if not music_info:
            logger.error(f"❌ Không tìm thấy bài hát: {query}")
            await send_temp_message(interaction, "❌ Không tìm thấy bài hát")
            return
        
        request_info = map_request_info(music_info, interaction.user)

        self.music_state.add_to_queue(request_info)
        logger.info(f"➕ Added to queue: {music_info}")
        await send_temp_message(interaction, f"➕ Đã thêm: {music_info}")

        if not self.music_state.is_playing:
            await self._play_next(interaction)

    async def skip(self, interaction: discord.Interaction):
        """Handle skip command"""
        self.last_interaction = interaction
        if not self.voice_client or not self.voice_client.is_playing():
            logger.error("❌ Không có bài hát nào đang phát")
            await send_temp_message(interaction, "❌ Không có bài hát nào đang phát")
            return

        # await send_temp_message(interaction, "⏭️ Đã chuyển bài!")
        self.voice_client.stop()
        # await self._play_next(interaction)
        
    async def _play_music(self, interaction: discord.Interaction, request_info: RequestInfo):
        """Play a single music track"""
        self.music_state.is_playing = True
        music_info = request_info.music_info
        if not await self._ensure_voice_client(interaction):
            return

        logger.info(f"🎵 Start playing: {music_info.title}")
        logger.info(f"🎧 Channel: {interaction.user.voice.channel.name}")
        logger.info(f"👤 Requested by: {interaction.user.display_name}")
        
        audio_source = discord.FFmpegPCMAudio(
            music_info.url,
            **FFMPEG_OPTIONS
        )

        def play_in_thread():
            start_time = time.time()
            try:
                # Phát nhạc trong thread riêng
                self.voice_client.play(audio_source, after=after_playing)
                # Đợi cho đến khi bài hát kết thúc
                while self.voice_client and self.voice_client.is_playing():
                    threading.Event().wait(1)
                    time_played = min(int(time.time() - start_time), music_info.duration - 1)
                    # Sử dụng run_coroutine_threadsafe để gọi coroutine từ thread
                    future = asyncio.run_coroutine_threadsafe(
                        self._update_player_ui(interaction, request_info, time_played),
                        interaction.client.loop,
                    )
                    try:
                        future.result()  # Đợi kết quả
                    except Exception as e:
                        logger.error(f"Error updating UI: {e}")
            except Exception as e:
                logger.error(f"Error in player thread: {e}")

        def after_playing(error):
            if error:
                logger.error(f"Error playing audio: {error}")
            
            future = asyncio.run_coroutine_threadsafe(
                self._play_next(self.last_interaction), 
                self.last_interaction.client.loop
            )
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in after_playing: {e}")

        # Hủy task cũ nếu có
        if self.current_player_task:
            self.current_player_task.cancel()
        
        # Tạo task mới trong thread pool
        self.current_player_task = self.player_thread_pool.submit(play_in_thread)

    async def _ensure_voice_client(self, interaction: discord.Interaction) -> bool:
        """Ensure bot is connected to voice channel"""
        if not interaction.user.voice:
            await send_temp_message(interaction, "❌ Bạn cần vào kênh thoại trước")
            return False

        voice_channel = interaction.user.voice.channel
        if not self.voice_client:
            self.voice_client = await voice_channel.connect()
        elif self.voice_client.channel != voice_channel:
            await self.voice_client.move_to(voice_channel)
        return True

    async def _update_player_ui(self, interaction, request_info, time_played=0):
        """Update music player UI"""
        embed = await create_now_playing_embed(request_info, time_played)
        view = MusicControlButtons(self.voice_client, self)
        
        if self.music_state.current_message:
            await self.music_state.current_message.edit(embed=embed, view=view)
        else:
            message = await interaction.followup.send(embed=embed, view=view)
            self.music_state.current_message = message

    async def _play_next(self, interaction: discord.Interaction):
        """Play next song in queue"""
        if self.music_state.get_queue():
            request_info = self.music_state.remove_from_queue()
            await self._play_music(interaction, request_info)
        else:
            self.music_state.is_playing = False
            logger.info("🔚 Hết bài hát trong hàng đợi")
            await send_temp_message(interaction, "🔚 Hết bài hát trong hàng đợi")

    async def _handle_playback_finished(self):
        """Handle cleanup after song finishes"""
        if self.music_state.get_queue():
            logger.info(f"Playing next song in queue")
        else:
            self.music_state.is_playing = False
            logger.info("Queue is empty")

# Initialize single instance
player = MusicPlayer()

# Export functions for bot commands
async def play(interaction: discord.Interaction, query: str):
    await player.play(interaction, query)

async def skip(interaction: discord.Interaction):
    await player.skip(interaction)