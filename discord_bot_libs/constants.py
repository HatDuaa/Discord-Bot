


from enum import Enum
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

    WATERMARK = f'Develeoped by {NAME}'

    

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

class Embed(Enum):
    MAX_LENGTH = 60


    def __str__(self):
        return self.value
    
class ProcessBar(Enum):
    """Enum for process bar
    
    Filled Characters:
        █ (Full block)
        ▰ (Black square with white)
        ■ (Black square)
        ━ (Heavy horizontal)
        ═ (Double horizontal)
        ▬ (Black horizontal rectangle)
        ● (Black circle)
        ▮ (Black vertical rectangle)
        ◾ (Black small square)
    Empty Characters:
        ░ (Light shade)
        ▱ (White square with black)
        □ (White square)
        ─ (Light horizontal)
        ▭ (White rectangle)
        ○ (White circle)
        ▯ (White vertical rectangle)
        ◽ (White small square)
    Cursor:
        🔘 (Radio button)
        ⚪ (Medium white circle)
        ● (Black circle)
        ◉ (Fisheye)
        ◆ (Black diamond)
        ◈ (White diamond containing black)
        ▶ (Black right-pointing triangle)
        ⭐ (Star)
    """

    FULL_BLOCK = '█'
    BLACK_SQUARE_WITH_WHITE = '▰'
    BLACK_SQUARE = '■'
    HEAVY_HORIZONTAL = '━'
    DOUBLE_HORIZONTAL = '═'
    BLACK_HORIZONTAL_RECTANGLE = '▬'
    BLACK_CIRCLE = '●'
    BLACK_VERTICAL_RECTANGLE = '▮'
    BLACK_VERTICAL_RECTANGLE_MEDIUM = '■'
    BLACK_SMALL_SQUARE = '◾'

    LIGHT_SHADE = '░'
    WHITE_SQUARE_WITH_BLACK = '▱'
    WHITE_SQUARE = '□'
    LIGHT_HORIZONTAL = '─'
    WHITE_RECTANGLE = '▭'
    WHITE_CIRCLE = '○'
    WHITE_VERTICAL_RECTANGLE = '▯'
    WHITE_VERTICAL_RECTANGLE_MEDIUM = '□'
    WHITE_SMALL_SQUARE = '◽'

    RADIO_BUTTON = '🔘'
    MEDIUM_WHITE_CIRCLE = '⚪'
    FISHEYE = '◉'
    BLACK_DIAMOND = '◆'
    WHITE_DIAMOND_CONTAINING_BLACK = '◈'
    BLACK_WHITE_VERTICAL_RECTANGLE_MEDIUM = '◧'
    BLACK_RIGHT_POINTING_TRIANGLE = '▶'
    STAR = '⭐'

    BAR_LENGTH = 20

    def __str__(self):
        return self.value
