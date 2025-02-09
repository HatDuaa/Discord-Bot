import discord
from discord.ext import commands
from loguru import logger

from config import SERVER_ID
from discord_bot_libs.manager import bot_manager, music_manager



class Client(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f"Bot is ready as {self.user}")
        try:
            guild = discord.Object(id=SERVER_ID)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        await bot_manager.on_message(message)
    
    async def on_reaction_add(self, reaction, user):
        await bot_manager.on_reaction_add(reaction, user)




intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True


client = Client(command_prefix='/', intents=intents)


logger.info(f"Bot_client will only work in server with ID: {SERVER_ID}")
GUILD_ID = discord.Object(id=SERVER_ID)



@client.tree.command(name='hello', description='Say hello to the bot', guild=GUILD_ID)
async def say_hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! I am a Hạt_Bí's bot.")

@client.tree.command(name='ping', description='Ping the bot', guild=GUILD_ID)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@client.tree.command(name='printer', description='Print the message', guild=GUILD_ID)
async def printer(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

@client.tree.command(name='play', description='Play music from YouTube', guild=GUILD_ID)
async def play_music(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    await music_manager.play(interaction, query)