#!/usr/bin/env python

"""smcplayer description"""

import sys

from os import listdir
from os.path import isfile, join

from smcplayer.player import FileLoader, Track, Playlist
from smcplayer.tui import TUI


def run():
    args = sys.argv[1:]
    path = "."
    if args:
        path = args[0]

    playlist = Playlist()
    playlist += [Track(FileLoader(join(path, file)))
                 for file in listdir(path)
                 if isfile(join(path, file)) and file.endswith(".mp3")]
    playlist.sort(key=lambda i: i.name)

    if not playlist:
        exit("MP3 files not found!")

    tui = TUI(playlist)
    tui.start()


if __name__ == "__main__":
    run()
