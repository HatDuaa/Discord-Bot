


import discord


class RunningEnvironment():
	TESTING = 'test'
	DEPLOY = 'deploy'


class TimeConfig:
	HUMAN_READABLE_HOUR_MIN_SECOND = '%H:%M:%S'
	HUMAN_READABLE_HOUR_MIN = '%H:%M'
	HUMAN_READABLE_DATE = '%Y-%m-%d'

class Author:
    NAME = 'Hạt Bí'
    DISCORD_ID = '546919469470056448'
    USER_URL = f'https://discord.com/users/{DISCORD_ID}'
    _avatar_url = None  # Cache avatar URL

    @classmethod
    async def initialize(cls, client: discord.Client):
        """Initialize author info once when bot starts"""
        if not cls._avatar_url:
            try:
                user = await client.fetch_user(int(cls.DISCORD_ID))
                cls._avatar_url = user.display_avatar.url
            except Exception as e:
                print(f"Error fetching author avatar: {e}")
                cls._avatar_url = None

    @classmethod
    async def get_avatar_url(cls) -> str:
        """Get cached avatar URL"""
        return cls._avatar_url
