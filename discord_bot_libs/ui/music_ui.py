import discord

from discord_bot_api.model.music_model import MusicInfo


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

def create_now_playing_embed(music_info: MusicInfo) -> discord.Embed:
    """Create an embed for the now playing message"""
    embed = discord.Embed(
        title=music_info.title, 
        url=music_info.webpage_url, 
        description="🎵 Đang phát", 
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=music_info.thumbnail)
    return embed