import os
import pygame

from io import BytesIO
from copy import deepcopy
from typing import List

from smcplayer.event import Event


SONG_END = pygame.USEREVENT + 1


class FileLoader:
    def __init__(self, file):
        if os.path.exists(file):
            self.name = os.path.basename(file)
            if file.endswith('.mp3'):
                self.file = file

    def get_name(self):
        # todo: add name from mp3 tags
        return self.name

    def get_source(self):
        """make source as file-like object"""
        with open(self.file, "rb") as f:
            result = BytesIO(f.read())
        return result


class Track:
    def __init__(self, loader):
        self.name = loader.get_name()
        self.source = loader.get_source()


class Playlist(List):
    def __init__(self, *args, **kwargs):
        self.init_mixer()
        self.current = 0

        self.event_song_start = Event()
        self.event_song_end = Event()
        self.event_song_end += self.next

        super(Playlist, self).__init__(*args, **kwargs)

    def init_mixer(self):
        pygame.init()
        BUFFER = 3072  # audio buffer size, number of samples since pygame 1.8.
        FREQ, SIZE, CHAN = pygame.mixer.get_init()
        pygame.mixer.init(FREQ, SIZE, CHAN, BUFFER)

    def play(self):
        track = self[self.current]
        track.source.seek(0)
        pygame.mixer.music.load(deepcopy(track.source))
        pygame.mixer.music.play()
        # pygame.mixer.music.set_pos(36)
        pygame.mixer.music.set_endevent(SONG_END)
        self.event_song_start(self.current)

    def player_event_loop(self):
        events = pygame.event.get()
        for event in events:
            if event.type in [SONG_END, ]:
                self.event_song_end(self.current)

    def next(self, *args, **kwargs):
        if self.current < len(self) - 1:
            self.current += 1
        else:
            self.current = 0
        self.play()

    def back(self):
        if self.current > 0:
            self.current -= 1
        else:
            self.current = len(self) - 1
        self.play()

    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
