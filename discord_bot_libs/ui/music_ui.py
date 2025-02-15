import discord
from loguru import logger

from discord_bot_api.model.music_model import MusicInfo, RequestInfo
from discord_bot_libs.constants import Author, Embed, ProcessBar, TimeConfig


class MusicControlButtons(discord.ui.View):
    def __init__(self, voice_client: discord.VoiceClient, music_manager=None):
        super().__init__(timeout=None)
        self.voice_client = voice_client
        self.music_manager = music_manager

    @discord.ui.button(label="⏭️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        logger.info("Previous button clicked")
        
        try:
            await self.music_manager.previous(interaction)
        except Exception as e:
            logger.error(f"Error in previous button: {e}")
            await interaction.followup.send("❌ An error occurred while previousing", ephemeral=True)

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        logger.info("Pause button clicked")
        
        if self.voice_client.is_playing():
            self.voice_client.pause()
            button.label = "▶️ Play"
        else:
            self.voice_client.resume()
            button.label = "⏸️ Pause"
            
        await interaction.message.edit(view=self)

    @discord.ui.button(label="⏭️ Next", style=discord.ButtonStyle.secondary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        logger.info("Next button clicked")
        
        try:
            await self.music_manager.skip(interaction)
        except Exception as e:
            logger.error(f"Error in skip button: {e}")
            await interaction.followup.send("❌ An error occurred while skipping!", ephemeral=True)


class MusicEmbed:
    """Class to handle music embed creation and formatting"""
    @staticmethod
    async def create_now_playing(request_info: RequestInfo, time_played: int) -> discord.Embed:
        music_info = request_info.music_info
        embed = discord.Embed(
            title=music_info.title,
            url=music_info.webpage_url,
            color=discord.Color.pink()
        )
        
        await MusicEmbed._add_requester(embed, request_info)
        MusicEmbed._add_thumbnail(embed, music_info)
        # MusicEmbed._add_space(embed)
        MusicEmbed._add_progress_bar(embed, music_info, time_played)
        MusicEmbed._add_track_info(embed, music_info)
        MusicEmbed._add_space(embed)
        await MusicEmbed._add_footer(embed)
        
        return embed
    
    @staticmethod
    async def create_queue(queue: list[RequestInfo]) -> discord.Embed:
        embed = discord.Embed(
            title="🎵 Danh sách hàng đợi",
            color=discord.Color.pink()
        )
        
        for i, request_info in enumerate(queue):
            music_info = request_info.music_info
            embed.add_field(
                name=f"{i + 1}. {music_info.title}",
                value=f"👤 {request_info.requester.display_name}",
                inline=False
            )

        await MusicEmbed._add_footer(embed)
        return embed

    @staticmethod
    async def _add_requester(embed: discord.Embed, request_info: RequestInfo):
        embed.set_author(
            name=f"Requested by {request_info.requester.display_name}",
            icon_url=request_info.requester.display_avatar.url
        )

    @staticmethod
    def _add_thumbnail(embed: discord.Embed, music_info: MusicInfo):
        if music_info.thumbnail:
            hq_thumbnail = music_info.thumbnail.replace('hqdefault', 'maxresdefault')
            embed.set_thumbnail(url=hq_thumbnail)

    @staticmethod
    def _add_progress_bar(embed: discord.Embed, music_info: MusicInfo, time_played: int):
        process_bar = UIHelper.generate_process_bar(music_info.duration, time_played)
        time_display = UIHelper.format_time_display(time_played, music_info._duration())
        embed.add_field(
            name="",
            value=f"{process_bar}   {time_display}",
            inline=False
        )

    @staticmethod
    def _add_track_info(embed: discord.Embed, music_info: MusicInfo):
        if music_info.channel:
            embed.add_field(name="📺 Channel", value=music_info.channel, inline=True)
        if music_info.view_count:
            view_count = format(music_info.view_count, ',d')
            embed.add_field(name="👀 Views", value=view_count, inline=True)

    @staticmethod
    def _add_space(embed: discord.Embed):
        embed.add_field(name="\u200b", value="\u200b", inline=False)

    @staticmethod
    async def _add_footer(embed: discord.Embed):
        embed.set_footer(
            text=f"{Author.WATERMARK}",
            icon_url=await Author.get_avatar_url()
        )

class UIHelper:
    """Helper class for UI-related utilities"""
    @staticmethod
    def generate_process_bar(duration: int, time_played: int) -> str:
        progress = time_played / duration
        bar_length = ProcessBar.BAR_LENGTH.value
        progress_position = int(progress * bar_length)
        
        loaded = str(ProcessBar.BLACK_SQUARE_WITH_WHITE) * progress_position
        remaining = str(ProcessBar.WHITE_SQUARE_WITH_BLACK) * (bar_length - progress_position)
        cursor = str(ProcessBar.BLACK_WHITE_VERTICAL_RECTANGLE_MEDIUM)
        # logger.debug(f"{loaded}{cursor}{remaining}")
        return f"{loaded}{cursor}{remaining}"

    @staticmethod
    def format_time_display(current: int, total: str) -> str:
        current_formatted = UIHelper.convert_seconds_to_time(current)
        return f"{current_formatted} / {total}"

    @staticmethod
    def convert_seconds_to_time(seconds: int) -> str:
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02d}"