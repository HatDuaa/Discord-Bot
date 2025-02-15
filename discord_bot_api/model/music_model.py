from datetime import datetime
from loguru import logger
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from collections import deque
import discord

class MusicInfo(BaseModel):
    title: str
    url: str
    thumbnail: str
    webpage_url: str
    duration: int

    view_count: int = 0
    like_count: int = 0
    channel: str = "Unknown"
    channel_url: str = ""
    upload_date: str = ""
    description: str = ""
    
    def __str__(self):
        minutes, seconds = divmod(self.duration, 60)
        return f'{self.title} | {int(minutes)}:{int(seconds):02d}'
    
    def _duration(self):
        minutes, seconds = divmod(self.duration, 60)
        return f'{int(minutes)}:{int(seconds):02d}'
    

class RequestInfo(BaseModel):
    music_info: MusicInfo
    requester: discord.Member
    time: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)



class MusicState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MusicState, cls).__new__(cls)
            cls._instance._queue = deque()
            cls._instance._history = deque()
            cls._instance._current_message = None
            cls._instance._is_playing = False
            cls._instance._current_track = None
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
    
    def next_track(self):
        if self._queue:
            track = self._queue.popleft()
            self._current_track = track
            self.add_to_history(track)
            return track
        return None
    
    def remove_previous_track(self) -> Optional[RequestInfo]:
        if self._history:
            track = self._history.popleft()
            return track
        return None
    
    def add_track(self, request_info: RequestInfo, position: int = -1):
        if position == -1:
            self._queue.append(request_info)
        elif position >= len(self._queue):
            self._queue.append(request_info)
        else:
            self._queue.insert(position, request_info)
        return position if position != -1 else len(self._queue)
    
    def remove_track(self, position: int):
        if 0 <= position < len(self._queue):
            return self._queue.pop(position)
        return None
    
    def get_queue(self) -> List[RequestInfo]:
        return list(self._queue)
    
    def get_history(self) -> List[RequestInfo]:
        return list(self._history)
    
    def clear_queue(self):
        self._queue.clear()
    
    def add_to_history(self, request_info: RequestInfo):
        logger.debug(f"Add to history: {request_info.music_info.title}")
        self._history.appendleft(request_info)
    
    def clear_history(self):
        self._history.clear()


def map_music_info(info) -> MusicInfo:
    return MusicInfo(
        title=info['title'],
        url=info['url'],
        thumbnail=info['thumbnail'],
        webpage_url=info['webpage_url'],
        duration=info['duration'],

        view_count=info.get('view_count', 0),
        like_count=info.get('like_count', 0),
        channel=info.get('uploader', 'Unknown'),
        channel_url=info.get('uploader_url', ''),
        upload_date=info.get('upload_date', ''),
        description=info.get('description', '')
    )

def map_request_info(music_info: MusicInfo, requester: discord.Member, time: datetime = datetime.now()) -> RequestInfo:
    return RequestInfo(
        music_info=music_info,
        requester=requester,
        time=time
    )