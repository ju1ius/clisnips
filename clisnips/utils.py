from __future__ import division

from decimal import Decimal

import gtk
import pango


def get_num_decimals(n):
    if isinstance(n, float):
        decimal_part = str(float(Decimal(n) % 1))
        return len(decimal_part.split('.')[1])
    return 0


# ========== Fonts & Colors helpers


def parse_color(spec):
    if isinstance(spec, gtk.gdk.Color):
        return spec
    return gtk.gdk.color_parse(spec)


def parse_font(spec):
    if isinstance(spec, pango.FontDescription):
        return spec
    return pango.FontDescription(spec)


# 65535. Set this to 255 to work with 8bit integers.
# Reminder:
# 8bit to 16bit:
# 255 << 8 | 255
# >>> 65535
# 16bit to 8bit
# 65535 << 8
# >>> 255
MAX_COLOR_VALUE = 255 << 8 | 255
HALF_MAX_COLOR_VALUE = MAX_COLOR_VALUE / 2


def get_contrast_fgcolor(color):
    """
    Returns either black or white, depending on the
    perceptive luminance of the given color:
    bright colors => black font
    dark colors => white font
    """
    # Counting the perceptive luminance - human eye favors green color...
    luminance = get_luminance(color)
    v = 0 if luminance > 0.5 else MAX_COLOR_VALUE
    return gtk.gdk.Color(red=v, green=v, blue=v)


def interpolate_colors(c1, c2, distance):
    """
    Returns a color at the given distance between c1 and c2.
    distance must be a float between 0.0 and 1.0
    """
    c1, c2 = parse_color(c1), parse_color(c2)

    r = c1.red + distance * (c2.red - c1.red)
    g = c1.green + distance * (c2.green - c1.green)
    b = c1.blue + distance * (c2.blue - c1.blue)

    return gtk.gdk.Color(red=int(r), green=int(g), blue=int(b))


def get_luminance(color):
    """
    Returns the perceptive luminance of a rgb color.
    """
    c = parse_color(color)
    yiq = ((c.red * 299) + (c.green * 587) + (c.blue * 114)) / 1000
    return yiq / MAX_COLOR_VALUE
