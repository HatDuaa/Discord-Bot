from datetime import datetime
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
    
    def add_to_queue(self, request_info: RequestInfo):
        self._queue.append(request_info)
        return len(self._queue)
    
    def add_to_queue_front(self, request_info: RequestInfo):
        self._queue.appendleft(request_info)
        return len(self._queue)
    
    def remove_from_queue(self) -> Optional[RequestInfo]:
        if self._queue:
            return self._queue.popleft()
        return None
    
    def get_queue(self) -> List[RequestInfo]:
        return list(self._queue)
    
    def clear_queue(self):
        self._queue.clear()
    
    def add_to_history(self, request_info: RequestInfo):
        self._history.appendleft(request_info)
    
    def get_previous(self) -> Optional[RequestInfo]:
        if self._history:
            return self._history.popleft()
        return None
    
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