from __future__ import annotations
from urwid import *
from placerank.tui.events import Events

class SearchTextField(Edit):
    def keypress(self, size, key):
        if key != 'enter':
            return super().keypress(size, key)
        Events.SEARCH.value.notify(super().edit_text)

class SearchBar(WidgetWrap):
    def __init__(self):
        text_field = Edit('Textual search: ')
        search_button = Button('Go')
        component = Filler(
            Columns((
                text_field,
                (7, search_button)
            ))
        )
        WidgetWrap.__init__(self, component)