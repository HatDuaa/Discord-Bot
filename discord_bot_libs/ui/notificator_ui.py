import discord
from loguru import logger


class Notificator:
    @staticmethod
    async def send_notification(channel: discord.TextChannel, title: str, description: str, color: discord.Color = discord.Color.blue()):
        """Send an embed notification to a specified channel"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        try:
            await channel.send(embed=embed)
            logger.info(f"Notification sent: {title}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")