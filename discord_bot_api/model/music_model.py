from pydantic import BaseModel
from typing import List, Optional

import discord

class MusicInfo(BaseModel):
    title: str
    url: str
    thumbnail: str
    webpage_url: str
    duration: int
    
    def __str__(self):
        return f'{self.title} | {self.duration}s'

class MusicState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicState, cls).__new__(cls)
            cls._instance._queue = []
            cls._instance._current_message = None
            cls._instance._is_playing = False
        return cls._instance
    
    @property
    def current_message(self) -> Optional[discord.Message]:
        return self._current_message
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing
    
    @is_playing.setter
    def is_playing(self, value: bool):
        self._is_playing = value
    
    @current_message.setter
    def current_message(self, message: discord.Message):
        self._current_message = message
    
    def add_to_queue(self, music_info: MusicInfo):
        self._queue.append(music_info)
    
    def remove_from_queue(self) -> Optional[MusicInfo]:
        if self._queue:
            return self._queue.pop(0)
        return None
    
    def get_queue(self) -> List[MusicInfo]:
        return self._queue.copy()
    
    def clear_queue(self):
        self._queue.clear()


def map_music_info(info) -> MusicInfo:
    return MusicInfo(
        title=info['title'],
        url=info['url'],
        thumbnail=info['thumbnail'],
        webpage_url=info['webpage_url'],
        duration=info['duration']
    )