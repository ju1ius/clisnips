import urwid as _urwid
from urwid.util import StoppingContext as _StoppingContext


# TODO: remove this when PR is released, see https://github.com/urwid/urwid/pull/401
def __base_screen_start(self, *args, **kwargs):
    if not self._started:
        self._started = True
        self._start(*args, **kwargs)
    return _StoppingContext(self)


_urwid.display_common.BaseScreen.start = __base_screen_start
