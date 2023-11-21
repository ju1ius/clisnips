import enum
import math
import sys
import time


class Direction(enum.StrEnum):
    UP = enum.auto()
    DOWN = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()


class Action(enum.StrEnum):
    MOVE = enum.auto()
    SCROLL = enum.auto()


class NavigationCommand:
    def __init__(self, action: Action, direction: Direction, offset: int | str):
        self.action = action
        self.direction = direction
        self.offset = offset


class InputProcessor:
    """
    Implements support for VIM style keys & basic commands.
    Supported keys:
        j,k - scroll 1 row up/down
        h,l - scroll 1 column left/right
        ctrl-[u/d] - scroll rows page up/down
        0 - go to first column
        $ - go to last column
        G - go to last row
    Supported commands:
        [number]j/k/h/l - scroll [number] rows/columns
        gg - go to first row
    """

    def __init__(self):
        self._last_key_press = -math.inf
        self._pending_command = ''
        self._key_directions = {
            'home': Direction.UP,
            'ctrl u': Direction.UP,
            'up': Direction.UP,
            'k': Direction.UP,
            'page up': Direction.UP,
            'end': Direction.DOWN,
            'down': Direction.DOWN,
            'j': Direction.DOWN,
            'ctrl d': Direction.DOWN,
            'G': Direction.DOWN,
            'page down': Direction.DOWN,
            'left': Direction.LEFT,
            '0': Direction.LEFT,
            'h': Direction.LEFT,
            'ctrl left': Direction.LEFT,
            'right': Direction.RIGHT,
            '$': Direction.RIGHT,
            'l': Direction.RIGHT,
            'ctrl right': Direction.RIGHT,
        }
        self._single_offset_keys = {'up', 'down', 'left', 'right', 'j', 'k', 'h', 'l'}
        self._max_offset_keys = {'home', 'end', 'ctrl left', 'ctrl right', '0', '$', 'G'}
        self._page_offset_keys = {'page up', 'page down', 'ctrl u', 'ctrl d'}
        self._command_keys = {'g'} | {str(i) for i in range(1, 10)}

    def process_key(self, key: str) -> NavigationCommand | None:
        if not self._pending_command:
            if key in self._single_offset_keys:
                return NavigationCommand(Action.MOVE, self._key_directions[key], 1)
            if key in self._max_offset_keys:
                return NavigationCommand(Action.MOVE, self._key_directions[key], sys.maxsize)
            if key in self._page_offset_keys:
                return NavigationCommand(Action.MOVE, self._key_directions[key], 'page')
            if key in self._command_keys:
                self._last_key_press = time.time()
                self._pending_command = key
                return None
            return None

        diff = time.time() - self._last_key_press
        if diff > self._timeout(key):
            self._clear_pending_command()
            return None

        return self._process_command(key)

    def _timeout(self, key: str) -> float:
        if self._pending_command.isdigit():
            return 1.0
        return 0.25

    def _clear_pending_command(self):
        self._pending_command = ''
        self._last_key_press = -math.inf

    def _process_command(self, key: str) -> NavigationCommand | None:
        if key == 'esc':
            self._clear_pending_command()
            return

        if self._pending_command.isdigit() and key.isdigit():
            self._pending_command += key
            return

        if self._pending_command.isdigit() and not key.isdigit():
            offset = int(self._pending_command)
            self._clear_pending_command()

            if key not in self._key_directions:
                return
            return NavigationCommand(Action.SCROLL, self._key_directions[key], offset)

        if self._pending_command == 'g' and key == 'g':
            self._clear_pending_command()
            return NavigationCommand(Action.SCROLL, Direction.UP, sys.maxsize)
