import random as r


def fate():
    return 0x80B0FF


def luck():
    return 0x9EAFE3


def random():
    return r.randint(0, 0xFFFFFF)


def red():
    return 0xFF0000


def pink():
    return 0xFC88FF


def orange():
    return 0xFF6800


def yellow():
    return 0xFFD800


def green():
    return 0x39FF14


def lime_green():
    return 0xB8FF00


def dark_green():
    return 0x006400


def blue():
    return 0x0000FF


def cyan():
    return 0x00FFFF


def purple():
    return 0x9400D3


def black():
    return 0x000001


def white():
    return 0xFFFFFF


def tan():
    return 0xFFC8B0


def light_gray():
    return 0xD3D3D3


def color_roles():
    return {
        "Blood Red": 0xFF0000,
        "Orange": 0xFF5B00,
        "Bright Yellow": 0xFFFF00,
        "Dark Yellow": 0xFFD800,
        "Light Green": 0x00FF00,
        "Dark Green": 0x009200,
        "Light Blue": 0x00FFFF,
        "Dark Blue": 0x0000FF,
        "Dark Purple": 0x9400D3,
        "Lavender": 0xDC91FF,
        "Hot Pink": 0xF47FFF,
        "Pink": 0xFF9DD1,
        "Black": 0x030303,
    }


class ColorSets:
    def rainbow(self):
        return [
            0xFF0000,
            0xFF002A,
            0xFF0055,
            0xFF007F,
            0xFF00AA,
            0xFF00D4,
            0xFF00FF,
            0xD500FF,
            0xAA00FF,
            0x8000FF,
            0x5500FF,
            0x2B00FF,
            0x0000FF,
            0x002AFF,
            0x0055FF,
            0x007FFF,
            0x00AAFF,
            0x00D4FF,
            0x00FFFF,
            0x00FFD5,
            0x00FFAA,
            0x00FF80,
            0x00FF55,
            0x00FF2B,
            0x00FF00,
            0x2AFF00,
            0x55FF00,
            0x7FFF00,
            0xAAFF00,
            0xD4FF00,
            0xFFFF00,
            0xFFD500,
            0xFFAA00,
            0xFF8000,
            0xFF5500,
            0xFF2B00,
        ]
