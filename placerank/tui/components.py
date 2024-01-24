from __future__ import annotations
from operator import mul
from tkinter import Label
from urwid import *
from placerank.tui.events import Events

PALETTE = [
    ('fg', 'black', 'light gray'),
    ('bg', 'black', 'dark magenta'),
    ('title', 'light magenta', 'light gray'),
    ('frame', 'white', 'light gray'),
]

class BaseContainer(Overlay):
    def __init__(self, top_widget: Widget, **kwargs):
        self.top_widget = LineBox(
            AttrMap(top_widget, 'fg'),
            title = 'Placerank',
            title_attr = 'title'
        )

        super().__init__(
            AttrMap(self.top_widget, 'frame'), AttrMap(SolidFill(), 'bg'),
            align = 'center', width = ('relative', 90),
            valign = 'middle', height = ('relative', 90),
            **kwargs
        )

class SearchBar(WidgetWrap):
    def __init__(self, **kwargs):
        self.text_field = Edit('Textual search: ', wrap='clip')
        self.search_button = Button('Go', on_press = lambda btn: Events.SEARCH.value.notify(self.text_field.edit_text))
        component = Filler(
            Columns((
                self.text_field,
                (7, self.search_button)
            )),
            **kwargs
        )
        WidgetWrap.__init__(self, component)
    
    def keypress(self, size, key):
        if key != 'enter': return super().keypress(size, key)
        Events.SEARCH.value.notify(self.text_field.edit_text)

class ResultArea(WidgetWrap):
    def __init__(self):
        ...

class Window(WidgetWrap):
    def __init__(self):
        self.search_bar = SearchBar(valign='top')
        self.base_container = BaseContainer(self.search_bar)
        WidgetWrap.__init__(self, self.base_container)