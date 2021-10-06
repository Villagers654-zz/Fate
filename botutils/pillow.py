"""
Pillow Utils
~~~~~~~~~~~~~

Helper functions for use with the Pillow/PIL module

:copyright: (C) 2020-present FrequencyX4
:license: Proprietary, see LICENSE for details
"""

from PIL import Image, ImageDraw


def add_corners(im, rad):
    """
    Adds transparent corners to an img
    :copyright: none, this function is open sourced and doesn't belong to me
    """
    circle = Image.new("L", (rad * 2, rad * 2), 0)
    d = ImageDraw.Draw(circle)
    d.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new("L", im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im
