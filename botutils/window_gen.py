import tkinter as tk
from tkinter import messagebox


class Window(tk.Tk):
	def __init__(self, width=300, height=500, top=0, *args, **kwargs):
		self._canvas = None
		self.width = width
		self.height = height
		self.center = width / 2
		self.top = top
		super().__init__(*args, **kwargs)

	@property
	def canvas(self):
		if not self._canvas:
			self._canvas = tk.Canvas(self, width=self.width, height=self.height)
		return self._canvas

	def pack(self):
		self.canvas.pack()

	def _get_pos(self, args, added=None):
		if not args:
			self.top += 20
			if added:
				self.top += added
			return self.center, self.top
		return args

	def warn(self, title, message):
		messagebox.showinfo(title, message)

	def label(self, text, position=None, **kwargs):
		label = tk.Label(self, text=text, **kwargs)
		self.canvas.create_window(*self._get_pos(position), window=label)
		return label

	def entry(self, position=None, *args, **kwargs):
		entry = tk.Entry(self, *args, **kwargs)
		self.canvas.create_window(*self._get_pos(position), window=entry)
		return entry

	def button(self, text, command, position=None, *args, **kwargs):
		button = tk.Button(text=text, command=command, *args, **kwargs)
		self.canvas.create_window(*self._get_pos(position, 10), window=button)
		return button
