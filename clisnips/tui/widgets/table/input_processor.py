import sys
import time
from enum import Enum
from typing import Union, Optional


class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class Action(Enum):
    MOVE = 'move'
    SCROLL = 'scroll'


class NavigationCommand:

    def __init__(self, action: Action, direction: Direction, offset: Union[int, str]):
        self.action = action,
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
        self._last_key_press = None
        self._pending_command = None
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
        self._single_offset_keys = ['up', 'down', 'left', 'right', 'j', 'k', 'h', 'l']
        self._max_offset_keys = ['home', 'end', 'ctrl left', 'ctrl right', '0', '$', 'G']
        self._page_offset_keys = ['page up', 'page down', 'ctrl u', 'ctrl d']

        self._digit_keys = [str(i) for i in range(1, 10)]
        self._command_keys = ['g']
        self._command_keys.extend(self._digit_keys)

    def process_key(self, key: str) -> Optional[NavigationCommand]:
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
        self._pending_command = None
        self._last_key_press = None

    def _process_command(self, key: str) -> Optional[NavigationCommand]:
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
