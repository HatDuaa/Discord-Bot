import discord
from loguru import logger

from discord_bot_api.model.music_model import MusicInfo, RequestInfo
from discord_bot_libs.constants import Author, Embed, ProcessBar, TimeConfig


class MusicControlButtons(discord.ui.View):
    def __init__(self, voice_client: discord.VoiceClient, music_manager=None):
        super().__init__(timeout=None)
        self.voice_client = voice_client
        self.music_manager = music_manager

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if self.voice_client.is_playing():
            self.voice_client.pause()
            button.label = "▶️ Play"
        else:
            self.voice_client.resume()
            button.label = "⏸️ Pause"
            
        await interaction.message.edit(view=self)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.secondary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            if self.voice_client and self.voice_client.is_playing():
                await self.music_manager.skip(interaction)
                await interaction.followup.send("⏭️ Đã chuyển bài!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Không có bài hát nào đang phát!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in skip button: {e}")
            await interaction.followup.send("❌ Có lỗi xảy ra khi skip!", ephemeral=True)



async def create_now_playing_embed(request_info: RequestInfo, time_played: int) -> discord.Embed:
    """Create an embed for the now playing message"""
    music_info = request_info.music_info
    
    # Create main embed with only title first
    embed = discord.Embed(
        title=music_info.title,  # Plain title
        url=music_info.webpage_url,  # URL will be attached to title
        color=discord.Color.purple()
    )

    # Set requester as author
    embed.set_author(
        name=f"Requested by {request_info.requester.display_name}",
        icon_url=request_info.requester.display_avatar.url
    )

    # Set image right after title/description
    if music_info.thumbnail:
        hq_thumbnail = music_info.thumbnail.replace('hqdefault', 'maxresdefault')
        embed.set_thumbnail(url=hq_thumbnail)
    
    # Progress bar in its own row
    process_bar = generate_process_bar(music_info.duration, time_played)
    embed.add_field(
        name="Progress",
        value=f"{process_bar}  {convert_seconds_to_human_readable(time_played)} / {music_info._duration()}",
        inline=False
    )

    # Add empty field as spacer after image
    embed.add_field(name="", value="", inline=False)

    # Now add all other fields
    if hasattr(music_info, 'channel'):
        embed.add_field(
            name="📺 Channel",
            value=music_info.channel,
            inline=True
        )
    
    if hasattr(music_info, 'view_count'):
        view_count = format(music_info.view_count, ',d')
        embed.add_field(
            name="👀 Views",
            value=view_count,
            inline=True
        )
    
    # Add empty field as spacer after image
    embed.add_field(name="", value=f"{Embed.MAX_LENGTH.value * ' '}", inline=False)

    # Set bot creator in footer
    embed.set_footer(
        text=f"{Author.WATERMARK}",
        icon_url=await Author.get_avatar_url()
    )

    return embed


def generate_process_bar(duration: int, time_played: int) -> str:
    progress = time_played / duration
    bar_length = ProcessBar.BAR_LENGTH.value
    progress_position = int(progress * bar_length)
    
    loaded = f"{ProcessBar.HEAVY_HORIZONTAL}" * progress_position
    remaining = f"{ProcessBar.LIGHT_HORIZONTAL}" * (bar_length - progress_position)
    cursor = f"{ProcessBar.BLACK_CIRCLE}"
    
    return f"{loaded}{cursor}{remaining}"


def convert_seconds_to_human_readable(seconds: int) -> str:
    """Convert seconds to human readable format"""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"