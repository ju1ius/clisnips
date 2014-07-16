import inspect
from operator import itemgetter

import gobject


class State(gobject.GObject):
    """
    A state object for applications
    """

    INITIAL = 0x0

    __gsignals__ = {
        'set-state': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_INT,)
        ),
        'enter-state': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_INT,)
        ),
        'leave-state': (
            gobject.SIGNAL_RUN_LAST,
            None,
            (gobject.TYPE_INT,)
        )
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self._mask = self.INITIAL
        self._states = None

    @classmethod
    def with_states(klass, *states):
        """
        Returns a new State instance, with the provided state names
        added as uppercased attributes. 
        """
        self = klass()
        for i, name in enumerate(states, start=1):
            setattr(self, name.upper(), 1 << i)
        return self

    def reset(self):
        self._mask = self.INITIAL
        self.emit('set-state', self.INITIAL)

    def get(self):
        """
        Gets the current state's bitmask.
        :returns: 
        """
        return self._mask

    def set(self, mask):
        """
        Sets the current state, clearing all other enterd states.
        :value: integer
        """
        self.emit('set-state', mask)
        self._mask = mask
        return self

    def enter(self, state):
        """
        Enters a new state by adding the given bit to the current bitmask.
        Emit the "enter-state" signal if we were not already
        in the given state.
        """
        if state not in self:
            self.emit('enter-state', state)
        self._mask |= state
        return self

    def leave(self, state):
        """
        Leaves the given state, by removing the given bit
        from the current bitmask.
        Emit the "leave-state" signal if we were in the given state.
        """
        if state in self:
            self.emit('leave-state', state)
        self._mask &= ~state
        return self

    def is_in(self, state):
        """
        Returns wheter the current state contains the given state.
        """
        return (self._mask & state) == state

    def __eq__(self, state):
        return self._mask == state

    def __contains__(self, state):
        return (self._mask & state) == state

    def __iadd__(self, state):
        return self.enter(state)

    def __isub__(self, state):
        return self.leave(state)

    def __int__(self):
        return self._mask

    def __str__(self):
        return hex(self._mask)

    def __repr__(self):
        fmt = '<{klass} mask:{mask}{states}>'
        states = ''.join(
            '\n    %s: %s%s' % (k, hex(v), ' *' if v in self else '')
            for k, v in self.get_states()
        )
        return fmt.format(klass=self.__class__.__name__,
                          mask=hex(self._mask),
                          states=states)

    # methods for debugging

    def get_states(self):
        if self._states is None:
            self._states = _get_states(self)
        return self._states

    def get_current_states(self):
        for name, value in self.get_states():
            if value in self:
                yield name, value


def _get_states(klass):
    if isinstance(klass, State):
        #FIXME: this conflicts with State.with_states factory method
        # and should be removed 
        klass = klass.__class__
    attrs = [a for a in
             inspect.getmembers(klass, lambda a: isinstance(a, int))
             if not a[0].startswith('_') and a[0].isupper()]
    return dict(sorted(attrs, key=itemgetter(1)))
