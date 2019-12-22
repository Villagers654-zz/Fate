import random as r

def fate():
	return 0x80b0ff

def luck():
	return 0x9eafe3

def random():
	return r.randint(0, 0xFFFFFF)

def red():
	return 0xff0000

def pink():
	return 0xfc88ff

def orange():
	return 0xff6800

def yellow():
	return 0xffd800

def green():
	return 0x39ff14

def lime_green():
	return 0xb8ff00

def dark_green():
	return 0x006400

def blue():
	return 0x0000FF

def cyan():
	return 0x00ffff

def purple():
	return 0x9400D3

def black():
	return 0x000001

def white():
	return 0xffffff

def tan():
	return 0xffc8b0

def light_gray():
	return 0xd3d3d3

def color_roles():
	return {
		'Blood Red': 0xff0000,
		'Orange': 0xff5b00,
		'Bright Yellow': 0xffff00,
		'Dark Yellow': 0xffd800,
		'Light Green': 0x00ff00,
		'Dark Green': 0x009200,
		'Light Blue': 0x00ffff,
		'Dark Blue': 0x0000ff,
		'Dark Purple': 0x9400d3,
		'Lavender': 0xdc91ff,
		'Hot Pink': 0xf47fff,
		'Pink': 0xff9dd1,
		'Black': 0x030303,
	}

class ColorSets:

	def rainbow(self):
		return [
        0xff0000,
        0xff002a,
        0xff0055,
        0xff007f,
        0xff00aa,
        0xff00d4,
        0xff00ff,
        0xd500ff,
        0xaa00ff,
        0x8000ff,
        0x5500ff,
        0x2b00ff,
        0x0000ff,
        0x002aff,
        0x0055ff,
        0x007fff,
        0x00aaff,
        0x00d4ff,
        0x00ffff,
        0x00ffd5,
        0x00ffaa,
        0x00ff80,
        0x00ff55,
        0x00ff2b,
        0x00ff00,
        0x2aff00,
        0x55ff00,
        0x7fff00,
        0xaaff00,
        0xd4ff00,
        0xffff00,
        0xffd500,
        0xffaa00,
        0xff8000,
        0xff5500,
        0xff2b00,
    ]
