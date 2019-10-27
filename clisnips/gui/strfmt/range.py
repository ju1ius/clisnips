from gi.repository import Gtk

from ...utils.number import get_num_decimals
from .field import SimpleField


class RangeField(SimpleField):

    def __init__(self, label: str, *args, **kwargs):
        entry = RangeEntry(*args, **kwargs)
        super().__init__(label, entry)


class RangeEntry(Gtk.SpinButton):

    def __init__(self, start, end, step, default=None):
        adjustment = Gtk.Adjustment(lower=start, upper=end, step_incr=step)
        decimals = get_num_decimals(step)
        super().__init__(adjustment=adjustment, digits=decimals)
        self.set_snap_to_ticks(True)
        if default is not None:
            self.set_value(default)

    def get_value(self):
        if self.get_digits() == 0:
            return super().get_value_as_int()
        return super().get_value()
