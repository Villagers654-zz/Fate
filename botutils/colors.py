
"""
Colors Shortcut
~~~~~~~~~~~~~~~~

Module for quick access to colors

:copyright: (C) 2019-present Michael Stollings
:license: Proprietary and Confidential, see LICENSE for details
"""

from random import randint


fate = 0x001269
luck = 0x9EAFE3
red = 0xFF0000
pink = 0xFC88FF
orange = 0xFF6800
yellow = 0xFFD800
green = 0x39FF14
lime_green = 0xB8FF00
dark_green = 0x006400
blue = 0x0000FF
cyan = 0x00FFFF
purple = 0x9400D3
black = 0x000001
white = 0xFFFFFF
tan = 0xFFC8B0
light_grey = 0xD3D3D3


def random():
    return randint(0, 0xFFFFFF)


def generate_rainbow_rgb(amount: int) -> list:
    fixed_colors = [
        (255, 0, 0),  # Red
        (255, 127, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),  # Green
        (0, 0, 255),  # Blue
        (75, 0, 130),  # Dark Purple
        (148, 0, 211),  # Purple
    ]
    color_array = []
    for iteration, (r, g, b) in enumerate(fixed_colors):
        color_array.append((r, g, b))
        if len(fixed_colors) != iteration + 1:
            nr, ng, nb = fixed_colors[iteration + 1]
            divide_into = int(amount / len(fixed_colors)) + 2
            r_diff = (nr - r) / divide_into
            g_diff = (ng - g) / divide_into
            b_diff = (nb - b) / divide_into
            for i in range(divide_into):
                r += r_diff
                g += g_diff
                b += b_diff
                color_array.append((int(r), int(g), int(b)))
    return color_array
