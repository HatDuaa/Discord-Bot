import discord

from discord_bot_api.model.music_model import MusicInfo, RequestInfo
from discord_bot_libs.constants import Author, TimeConfig


class MusicControlButtons(discord.ui.View):
    def __init__(self, voice_client: discord.VoiceClient):
        super().__init__(timeout=None)
        self.voice_client = voice_client

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

async def create_now_playing_embed(request_info: RequestInfo, time_played: int, client: discord.client) -> discord.Embed:
    """Create an embed for the now playing message"""
    music_info = request_info.music_info
    
    # Create main embed with only title first
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**[{music_info.title}]({music_info.webpage_url})**",  # Add separator
        color=discord.Color.purple()
    )
    
    # Set image right after title/description
    if music_info.thumbnail:
        hq_thumbnail = music_info.thumbnail.replace('hqdefault', 'maxresdefault')
        embed.set_image(url=hq_thumbnail)
    
    # Add empty field as spacer after image
    embed.add_field(name="", value="", inline=False)
    
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
    
    # # Status and Queue in same row
    # embed.add_field(
    #     name="Status",
    #     value="▶️ Playing",
    #     inline=True
    # )
    
    # embed.add_field(
    #     name="Queue Position",
    #     value="#1",
    #     inline=True
    # )

    # Footer at the bottom
    embed.set_footer(
        text=f"Requested by {request_info.requester.display_name} • {request_info.time.strftime(TimeConfig.HUMAN_READABLE_HOUR_MIN)}",
        icon_url=request_info.requester.display_avatar.url
    )

    # Add bot creator as author
    author_avatar = await Author.get_avatar_url()
    embed.set_author(
        name=Author.NAME,
        url=Author.USER_URL,
        icon_url=author_avatar
    )

    return embed


def generate_process_bar(duration: int, time_played: int) -> str:
    """Generate a progress bar for the music player"""
    progress = time_played / duration
    bar_length = 30
    progress_position = int(progress * bar_length)
    
    # Tạo thanh progress với 2 ký tự khác nhau
    loaded = "━" * progress_position  # Phần đã phát
    remaining = "─" * (bar_length - progress_position)  # Phần còn lại
    
    # Thêm cursor vào vị trí hiện tại
    return f"{loaded}▶{remaining}"


def convert_seconds_to_human_readable(seconds: int) -> str:
    """Convert seconds to human readable format"""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"