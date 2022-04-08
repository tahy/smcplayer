import curses

from smcplayer.event import Event


class TUIEventMixin:
    def key_up(self):
        self.selected_track = self.selected_track - (self.selected_track > 0 and 1 or 0)
        if self.selected_track == 0 and self.first_visible > 0:
            self.first_visible -= 1

    def key_down(self):
        self.selected_track = self.selected_track + \
                              (self.selected_track < self.playlist_height - 1 and 1 or 0)
        if self.selected_track + 1 >= self.playlist_height:
            if self.first_visible + self.playlist_height < len(self.playlist):
                self.first_visible += 1

    def key_enter(self):
        self.playlist.current = self.selected_track + self.first_visible
        self.playlist.play()

    def key_space(self):
        self.playlist.pause()

    def key_back(self):
        self.playlist.back()

    def key_tab(self):
        self.playlist.next()


class TUI(TUIEventMixin):
    def __init__(self, playlist):
        self.screen = None
        self.title = "STUPID CONSOLE MP3 PLAYER"
        self.status = "Press 'q' to exit | STATUS BAR | playing: {}"
        self.height = 0
        self.width = 0
        self.selected_track = 0
        self.first_visible = 0
        self.key = 0
        self.playlist_height = 1
        self.playlist = playlist

        self.event_key_up = Event()
        self.event_key_down = Event()
        self.event_key_enter = Event()
        self.event_key_space = Event()
        self.event_key_back = Event()
        self.event_key_tab = Event()

        self.event_key_up += self.key_up
        self.event_key_down += self.key_down
        self.event_key_enter += self.key_enter
        self.event_key_space += self.key_space
        self.event_key_back += self.key_back
        self.event_key_tab += self.key_tab

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
            self.listen_key_press()
            self.playlist.player_event_loop()
            self.render_screen()
            # Wait for next input
            self.key = self.screen.getch()

    def listen_key_press(self):
        if self.key == curses.KEY_DOWN:
            self.event_key_down()

        elif self.key == curses.KEY_UP:
            self.event_key_up()

        elif self.key == curses.KEY_BACKSPACE:
            self.event_key_back()

        elif self.key == curses.KEY_ENTER or self.key == 10 or self.key == 13:
            self.event_key_enter()

        elif self.key == ord(" "):
            self.event_key_space()

        elif self.key == ord("\t"):
            self.event_key_tab()

    def render_playlist(self):
        # height - title - status - progress bar
        self.playlist_height = self.height - 1 - 1 - 1
        self.playlist_height = min(self.playlist_height, len(self.playlist))

        for n in range(self.playlist_height):
            if n + self.first_visible == self.playlist.current:
                self.screen.attron(curses.color_pair(2))
                self.screen.attron(curses.A_BOLD)

            if n == self.selected_track:
                self.screen.attron(curses.color_pair(3))

            tack_no = n + self.first_visible
            self.screen.addstr(2 + n, 0, self.playlist[tack_no].name)
            self.screen.addstr(2 + n, len(self.playlist[tack_no].name),
                               " " * (self.width - len(self.playlist[tack_no].name)))
            self.screen.attroff(curses.color_pair(2))
            self.screen.attroff(curses.color_pair(3))
            self.screen.attroff(curses.A_BOLD)

    def render_statusbar(self):
        status = self.status.format(self.playlist[self.playlist.current].name)
        self.screen.attron(curses.color_pair(3))
        self.screen.addstr(self.height - 1, 0, status)
        self.screen.addstr(self.height - 1, len(status), " " * (self.width - len(status) - 1))
        self.screen.attroff(curses.color_pair(3))

    def render_header(self):
        self.screen.attron(curses.color_pair(1))
        self.screen.attron(curses.A_BOLD)
        self.screen.addstr(0, 0, self.title)
        self.screen.attroff(curses.color_pair(2))
        self.screen.attroff(curses.A_BOLD)

    def render_progressbar(self):
        self.screen.addstr(1, 0, "#" * self.width)

    def render_screen(self):
        self.render_header()
        self.render_progressbar()
        self.render_playlist()
        self.render_statusbar()
        self.screen.refresh()

    def start(self):
        curses.wrapper(self.run_screen)
