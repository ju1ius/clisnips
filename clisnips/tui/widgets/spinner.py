import urwid

from clisnips.tui.animation import AnimationController


class Spinner(urwid.Widget):
    _frames = ('⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷')

    _sizing = frozenset([urwid.FIXED])

    def __init__(self):
        self._canvas_cache = []
        self._current_frame = 0
        self._animation = AnimationController(self._update, 12)
        for i, frame in enumerate(self._frames):
            canvas = urwid.Text(self._frames[i]).render((3,))
            self._canvas_cache.append(canvas)

    def toggle(self):
        self._animation.toggle()

    def start(self):
        self._current_frame = 0
        self._animation.start()

    def stop(self):
        self._animation.stop()

    def render(self, size, focus=False):
        canvas = self._canvas_cache[self._current_frame]
        c = urwid.CompositeCanvas(canvas)
        pad_h = int((size[0] - 3) / 2)
        pad_v = int((size[1] - 1) / 2)
        c.pad_trim_left_right(pad_h, pad_h)
        c.pad_trim_top_bottom(pad_v, pad_v)
        return c

    def rows(self, size, focus=False):
        return 1

    def pack(self, size=None, focus=False):
        return 3, 1

    def _update(self, delta):
        self._current_frame = int(self._current_frame + delta) % len(self._frames)
        self._invalidate()
