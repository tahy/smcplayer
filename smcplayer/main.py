#!/usr/bin/env python

"""cplayer description"""

import curses
import os
import pygame
import sys

from io import BytesIO
from copy import deepcopy
from os import listdir
from os.path import isfile, join


SONG_END = pygame.USEREVENT + 1


class Event(object):

    def __init__(self):
        self.__eventhandlers = []

    def __iadd__(self, handler):
        self.__eventhandlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__eventhandlers.remove(handler)
        return self

    def __call__(self, *args, **keywargs):
        for eventhandler in self.__eventhandlers:
            eventhandler(*args, **keywargs)


class FileLoader:
    name = ""
    file = ""

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
        # result = None
        with open(self.file, "rb") as f:
            result = BytesIO(f.read())
        return result


class Track:
    name = ""
    source = ""

    def __init__(self, loader):
        self.name = loader.get_name()
        self.source = loader.get_source()


class Playlist:
    queue = []
    current = 0
    current_name = ""
    repeat = True

    def __init__(self):
        self.init_mixer()
        self.queue = []
        self.current = 0
        self.clock = pygame.time.Clock()
        self.repeat = True

        self.event_song_start = Event()
        self.event_song_end = Event()
        self.event_song_end += self.next

    def init_mixer(self):
        pygame.init()
        BUFFER = 3072  # audio buffer size, number of samples since pygame 1.8.
        FREQ, SIZE, CHAN = pygame.mixer.get_init()
        pygame.mixer.init(FREQ, SIZE, CHAN, BUFFER)

    def add_track(self, track):
        self.queue.append(track)

    def next(self, number):
        if self.current < len(self.queue) - 1:
            self.current += 1
        else:
            self.current = 0

        self.play()

    def play(self):
        track = self.queue[self.current]
        track.source.seek(0)
        pygame.mixer.music.load(deepcopy(track.source))
        pygame.mixer.music.play()
        # pygame.mixer.music.set_pos(36)
        pygame.mixer.music.set_endevent(SONG_END)
        self.event_song_start(self.current)

    def player_event_loop(self):
        events = pygame.event.get()
        # if events:
        #     print(events)
        for event in events:
            if event.type in [SONG_END, ]:
                self.event_song_end(self.current)

    # def stop(self):
    #     pygame.mixer.music.stop()

    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()


class TUI:
    screen = None
    title = "STUPID CONSOLE MP3 PLAYER"
    subtitle = "by Pavel Potapov"
    status = "Press 'q' to exit | STATUS BAR | playing: {}"
    height = 0
    width = 0
    selected_track = 0
    first_visible = 0
    key = 0
    playlist = None

    def __init__(self, playlist):
        self.playlist = playlist

    def render_screen(self):
        self.render_header()
        self.render_progressbar()
        self.render_playlist()
        self.render_statusbar()
        self.screen.refresh()

    def run_screen(self, screen):
        # Initialization
        self.screen = screen
        self.screen.clear()
        self.screen.refresh()
        self.screen.nodelay(True)
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.height, self.width = self.screen.getmaxyx()

        # Loop where k is the last character pressed
        while self.key != ord('q'):
            self.playlist.player_event_loop()
            self.render_screen()
            # Wait for next input
            self.key = self.screen.getch()

    def render_playlist(self):
        # height - title - status - progres bar
        playlist_height = self.height - 1 - 1 - 1
        playlist_height = min(playlist_height, len(self.playlist.queue))

        if self.key == curses.KEY_DOWN:
            self.selected_track = self.selected_track + \
                                  (self.selected_track < playlist_height - 1 and 1 or 0)
            if self.selected_track + 1 >= playlist_height:
                if self.first_visible + playlist_height < len(self.playlist.queue):
                    self.first_visible += 1

        elif self.key == curses.KEY_UP:
            self.selected_track = self.selected_track - (self.selected_track > 0 and 1 or 0)
            if self.selected_track == 0 and self.first_visible > 0:
                self.first_visible -= 1

        elif self.key == curses.KEY_BACKSPACE:
            pass

        elif self.key == curses.KEY_ENTER or self.key == 10 or self.key == 13:
            self.playlist.current = self.selected_track + self.first_visible
            self.playlist.play()

        elif self.key == ord(" "):
            self.playlist.pause()

        for n in range(playlist_height):
            if n + self.first_visible == self.playlist.current:
                self.screen.attron(curses.color_pair(2))
                self.screen.attron(curses.A_BOLD)

            if n == self.selected_track:
                self.screen.attron(curses.color_pair(3))

            tack_no = n + self.first_visible
            self.screen.addstr(2 + n, 0, self.playlist.queue[tack_no].name)
            self.screen.addstr(2 + n, len(self.playlist.queue[tack_no].name),
                               " " * (self.width - len(self.playlist.queue[tack_no].name)))
            self.screen.attroff(curses.color_pair(2))
            self.screen.attroff(curses.color_pair(3))
            self.screen.attroff(curses.A_BOLD)

    def render_statusbar(self):
        status = self.status.format(self.playlist.queue[self.playlist.current].name)
        self.screen.attron(curses.color_pair(3))
        self.screen.addstr(self.height - 1, 0, status)
        self.screen.addstr(self.height - 1, len(status), " " * (self.width - len(status) - 1))
        self.screen.attroff(curses.color_pair(3))

    def render_header(self):
        # Turning on attributes for title
        self.screen.attron(curses.color_pair(1))
        self.screen.attron(curses.A_BOLD)
        self.screen.addstr(0, 0, self.title)
        # Turning off attributes for title
        self.screen.attroff(curses.color_pair(2))
        self.screen.attroff(curses.A_BOLD)

    def render_progressbar(self):
        self.screen.addstr(1, 0, '#' * self.width)


def run():
    args = sys.argv[1:]
    path = "."
    if args:
        path = args[0]

    files = [f for f in listdir(path) if isfile(join(path, f)) and f.endswith(".mp3")]

    if not files:
        exit("MP3 files not found!")

    files.sort()
    playlist = Playlist()
    for file in files:
        track = Track(FileLoader(join(path, file)))
        playlist.add_track(track)

    tui = TUI(playlist)
    curses.wrapper(tui.run_screen)


if __name__ == "__main__":
    run()

