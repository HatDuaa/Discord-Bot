from concurrent.futures import ThreadPoolExecutor
import threading
import time
import discord
import asyncio
from loguru import logger
from typing import Optional

from discord_bot_api.model.music_model import MusicInfo, MusicState, RequestInfo, map_request_info
from discord_bot_libs.ui.music_ui import MusicControlButtons, MusicEmbed
from discord_bot_libs.utils import get_music_info, send_temp_embed

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class MusicPlayer:
    def __init__(self):
        self._initialize_state()
        self._initialize_thread_pool()

    def _initialize_state(self):
        self.music_state = MusicState()
        self.music_embed = MusicEmbed()
        self.voice_client: Optional[discord.VoiceClient] = None
        self.last_interaction: Optional[discord.Interaction] = None

    def _initialize_thread_pool(self):
        """Initialize thread pool with cleanup"""
        if hasattr(self, 'player_thread_pool'):
            # Shutdown existing pool
            self.player_thread_pool.shutdown(wait=False)
            
        if hasattr(self, 'current_player_task') and self.current_player_task:
            # Cancel current task
            self.current_player_task.cancel()
            self.current_player_task = None
            
        # Create new pool
        self.player_thread_pool = ThreadPoolExecutor(max_workers=1)

    async def play(self, interaction: discord.Interaction, query: str):
        """Handle play command with queue management"""
        self.last_interaction = interaction
        
        music_info = await self._fetch_music_info(query)
        if not music_info:
            return

        request_info = map_request_info(music_info, interaction.user)
        await self._handle_queue_addition(interaction, request_info)

        if not self.music_state.is_playing:
            await self._play_next(interaction)

    async def _fetch_music_info(self, query: str) -> Optional[MusicInfo]:
        music_info = await get_music_info(query)
        if not music_info:
            logger.error(f"❌ Không tìm thấy bài hát: {query}")
            await send_temp_embed(self.last_interaction, 'play', f"❌ Không tìm thấy bài hát")
            return None
        return music_info

    async def _handle_queue_addition(self, interaction: discord.Interaction, request_info: RequestInfo):
        position = self.music_state.add_to_queue(request_info)
        logger.info(f"➕ Added to queue: {request_info.music_info} | Position: {position}")
        await send_temp_embed(interaction, f"➕ Đã thêm", f"{request_info.music_info} | Vị trí: {position}", request_info.music_info.webpage_url)

    async def _play_next(self, interaction: discord.Interaction):
        """Play next song in queue"""
        if self.music_state.get_queue():
            request_info = self.music_state.remove_from_queue()
            await self._play_music(interaction, request_info)
        else:
            self.music_state.is_playing = False
            logger.info("🔚 Hết bài hát trong hàng đợi")
            await send_temp_embed(interaction, "🔚 Play next", "Hết bài hát trong hàng đợi")

    async def skip(self, interaction: discord.Interaction):
        """Handle skip command"""
        self.last_interaction = interaction
        await send_temp_embed(interaction, "⏭️ Chuyển bài")
        self.voice_client.stop()
        
    async def previous(self, interaction: discord.Interaction):
        """Handle previous command"""
        self.last_interaction = interaction
        previous_request = self.music_state.get_previous()
        if previous_request:
            self.music_state.add_to_queue_front(previous_request)
            await send_temp_embed(interaction, "⏮️ Quay lại bài trước!")
            self.voice_client.stop()
        else:
            await send_temp_embed(interaction, "⏮️ Previous", "❌ Không có bài hát trước đó trong lịch sử!")

    async def queue(self, interaction: discord.Interaction):
        """Handle queue command"""
        queue = self.music_state.get_queue()
        if not queue:
            await send_temp_embed(interaction, "Queue", "🔚 Hàng đợi trống!")
            return

        embed = await self.music_embed.create_queue(queue)
        await interaction.followup.send(embed=embed)

    async def _play_music(self, interaction: discord.Interaction, request_info: RequestInfo):
        """Play a single music track"""
        self.music_state.is_playing = True
        music_info = request_info.music_info

        # Force cleanup of previous playback
        self._initialize_thread_pool()

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
                self.voice_client.play(audio_source)
                # Đợi cho đến khi bài hát kết thúc
                while (self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused())):
                    if self.voice_client.is_playing():  # Only update UI when actually playing
                        time_played = min(int(time.time() - start_time), music_info.duration - 1)
                        future = asyncio.run_coroutine_threadsafe(
                            self._update_player_ui(interaction, request_info, time_played),
                            interaction.client.loop,
                        )
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error updating UI: {e}")
                    threading.Event().wait(10)

                # After playback finished
                logger.info(f"🔚 Kết thúc bài hát: {music_info.title}")
                # Add to history
                self.music_state.add_to_history(request_info)
                # Call after_playing in the same thread
                after_playing(None)
            except Exception as e:
                logger.error(f"Error in player thread: {e}")
                after_playing(e)  # Pass the error to after_playing

        def after_playing(error):
            """Handle completion of current track"""
            if error:
                logger.error(f"Error playing audio: {error}")
            logger.info(f"after_playing | music_info: {music_info}")
            future = asyncio.run_coroutine_threadsafe(
                self._play_next(self.last_interaction), 
                self.last_interaction.client.loop
            )
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in after_playing: {e}")
        
        # Tạo task mới trong thread pool
        self.current_player_task = self.player_thread_pool.submit(play_in_thread)

    async def _ensure_voice_client(self, interaction: discord.Interaction) -> bool:
        """Ensure bot is connected to voice channel"""
        if not interaction.user.voice:
            await send_temp_embed(interaction, "NOTI", "❌ Bạn cần vào kênh thoại trước")
            return False

        voice_channel = interaction.user.voice.channel
        if not self.voice_client:
            self.voice_client = await voice_channel.connect()
        elif self.voice_client.channel != voice_channel:
            await self.voice_client.move_to(voice_channel)
        return True

    async def _update_player_ui(self, interaction, request_info, time_played=0):
        """Update music player UI"""
        embed = await self.music_embed.create_now_playing(request_info, time_played)
        view = MusicControlButtons(self.voice_client, self)
        
        if self.music_state.current_message:
            try:
                await self.music_state.current_message.edit(embed=embed, view=view)
            except discord.errors.NotFound:
                # Message không còn tồn tại, gửi message mới
                message = await interaction.followup.send(embed=embed, view=view)
                self.music_state.current_message = message
            except discord.errors.HTTPException as e:
                logger.error(f"HTTPException when editing message: {e}")
                # Gửi message mới nếu có lỗi HTTP
                message = await interaction.followup.send(embed=embed, view=view)
                self.music_state.current_message = message
        else:
            message = await interaction.followup.send(embed=embed, view=view)
            self.music_state.current_message = message
    
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

async def previous(interaction: discord.Interaction):
    await player.previous(interaction)

async def queue(interaction: discord.Interaction):
    await player.queue(interaction)