from concurrent.futures import ThreadPoolExecutor
import threading
import time
import discord
import asyncio
from loguru import logger
from typing import Optional

from discord_bot_api.model.music_model import MusicInfo, MusicState, RequestInfo, map_request_info
from discord_bot_libs.constants import FFMPEG_OPTIONS
from discord_bot_libs.ui.music_ui import MusicControlButtons, MusicEmbed
from discord_bot_libs.utils import get_music_info, send_temp_embed, send_temp_noti



class AudioPlayer:
    def __init__(self, voice_client: discord.VoiceClient):
        self.time_played = 0
        self.voice_client = voice_client
        self._initialize_thread_pool()

    def _initialize_thread_pool(self):
        if hasattr(self, 'player_thread_pool'):
            self.player_thread_pool.shutdown(wait=False)
        if hasattr(self, 'current_player_task') and self.current_player_task:
            self.current_player_task.cancel()
            self.current_player_task = None
        self.player_thread_pool = ThreadPoolExecutor(max_workers=1)

    async def play(self, audio_source, on_play_callback, on_finish_callback):
        self._initialize_thread_pool()
        self.current_player_task = self.player_thread_pool.submit(
            self._play_in_thread, 
            audio_source, 
            on_play_callback,
            on_finish_callback
        )

    def _play_in_thread(self, audio_source, on_play_callback, on_finish_callback):
        start_time = time.time()
        try:
            self.voice_client.play(audio_source)
            while (self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused())):
                if self.voice_client.is_playing():
                    self.time_played = int(time.time() - start_time)
                    on_play_callback(self.time_played)
                threading.Event().wait(5)
            on_finish_callback(None)
        except Exception as e:
            logger.error(f"Error in player thread: {e}")
            on_finish_callback(e)

    async def get_time_played(self):
        return self.time_played
    

    
class MusicPlayer:
    def __init__(self):
        self.music_state = MusicState()
        self.music_embed = MusicEmbed()
        self.audio_player = None
        self.voice_client = None
        self.last_interaction = None
        self.current_message = None

    @staticmethod
    def set_interaction_wrapper():
        """Decorator to set the last interaction before executing a method"""
        def decorator(func):
            async def wrapper(self, *args, **kwargs):
                # Find interaction in args or kwargs
                interaction = next(
                    (arg for arg in args if isinstance(arg, discord.Interaction)),
                    kwargs.get('interaction', None)
                )
                if interaction:
                    self.last_interaction = interaction
                return await func(self, *args, **kwargs)
            return wrapper
        return decorator

    @set_interaction_wrapper()
    async def play(self, interaction: discord.Interaction, query: str):
        """Handle play command"""
        music_info = await self._fetch_music_info(query)
        if not music_info:
            return

        request_info = map_request_info(music_info, interaction.user)
        position = self.music_state.add_track(request_info)
        description = f"⏱️ {music_info._duration()} {' '*25} \t \t 📍 Position: {position}"
        logger.info(f"🎵 Added to queue: {music_info.title}")
        await send_temp_noti(interaction, f"➕ {music_info.title}", description, music_info.webpage_url)

        if not self.music_state.is_playing:
            await self._play_next(interaction)

    @set_interaction_wrapper()
    async def _play_next(self, interaction: discord.Interaction):
        """Play next track in queue"""
        if (self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused())):
            self.voice_client.stop()
            return
        request_info = self.music_state.next_track()
        if not request_info:
            await send_temp_noti(interaction, "🎵 No more songs in the queue!")
            self.music_state.is_playing = False
            return
        await self._play_music(interaction, request_info)
        
    
    @set_interaction_wrapper()
    async def skip(self, interaction: discord.Interaction):
        """Skip current track"""
        if not self.audio_player:
            logger.warning("No audio player to skip")
            return
        await self._play_next(interaction)


    @set_interaction_wrapper()
    async def previous(self, interaction: discord.Interaction):
        """Handle previous command"""
        logger.info("Previous command")
        previous_track = self.music_state.remove_previous_track()
        if previous_track:
            time_played = await self.audio_player.get_time_played()
            if time_played <= 30 and len(self.music_state.get_history()) > 0:
                previous_track = self.music_state.remove_previous_track()

            self.music_state.add_track(previous_track)
            await self._play_next(interaction)
        else:
            await send_temp_noti(interaction, "❌ Dont have previous track!")

    @set_interaction_wrapper()
    async def queue(self, interaction: discord.Interaction):
        """Handle queue command"""
        queue = self.music_state.get_queue()
        if not queue:
            await send_temp_noti(interaction, "🎵 The queue is null!")
            return

        embed = await self.music_embed.create_queue(queue)
        await send_temp_embed(interaction, embed)
    
    @set_interaction_wrapper()
    async def _play_music(self, interaction: discord.Interaction, request_info: RequestInfo):
        if not await self._ensure_voice_client(interaction):
            return

        self.music_state.is_playing = True
        logger.info(f"🎵 Start playing: {request_info.music_info.title}")
        logger.info(f"🎧 Channel: {interaction.user.voice.channel.name}")
        logger.info(f"👤 Requested by: {interaction.user.display_name}")

        if not self.audio_player:
            self.audio_player = AudioPlayer(self.voice_client)

        audio_source = discord.FFmpegPCMAudio(
            request_info.music_info.url,
            **FFMPEG_OPTIONS
        )

        def on_play(time_played):
            asyncio.run_coroutine_threadsafe(
                self._update_player_ui(interaction, request_info, time_played),
                self.last_interaction.client.loop
            )

        def on_finish(error):
            logger.info(f"🎵 Finished playing: {request_info.music_info.title}")
            if error:
                logger.error(f"Error playing audio: {error}")
            asyncio.run_coroutine_threadsafe(
                self._play_next(interaction),
                self.last_interaction.client.loop
            )

        await self.audio_player.play(audio_source, on_play, on_finish)

    async def _fetch_music_info(self, query: str) -> Optional[MusicInfo]:
        music_info = await get_music_info(query)
        if not music_info:
            logger.error(f"❌ No music found for: {query}")
            await send_temp_noti(self.last_interaction, 'Play', f"❌ No music found for: {query}")
            return None
        return music_info
    
    async def _ensure_voice_client(self, interaction: discord.Interaction) -> bool:
        """Ensure bot is connected to voice channel"""
        if not interaction.user.voice:
            await send_temp_noti(interaction, "NOTI", "❌ You are not in a voice channel!")
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
        
        if self.current_message:
            try:
                await self.current_message.edit(embed=embed, view=view)
            except discord.errors.NotFound:
                # Message không còn tồn tại, gửi message mới
                message = await interaction.followup.send(embed=embed, view=view)
                self.current_message = message
            except discord.errors.HTTPException as e:
                logger.error(f"HTTPException when editing message: {e}")
                # Gửi message mới nếu có lỗi HTTP
                message = await interaction.followup.send(embed=embed, view=view)
                self.current_message = message
        else:
            message = await interaction.followup.send(embed=embed, view=view)
            self.current_message = message
    

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