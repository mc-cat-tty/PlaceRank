from __future__ import annotations
from operator import mul
from tkinter import Label
from xml.dom.minidom import Document
from urwid import *
from placerank.tui.events import Events
from placerank.logic_views import DocumentLogicView

PALETTE = (
    ('fg', 'black', 'light gray'),
    ('bg', 'black', 'dark magenta'),
    ('title', 'light magenta', 'light gray'),
    ('frame', 'white', 'light gray'),
    ('btn', 'light magenta', 'light gray')
)

FIELDS = (CheckBox(c, True) for c in DocumentLogicView.SCHEMA.keys() if c != 'id')

class BaseContainer(Overlay):
    def __init__(self, top_widget: Widget, **kwargs):
        self.top_widget = LineBox(
            AttrMap(top_widget, 'fg'),
            title = 'Placerank',
            title_attr = 'title'
        )

        super().__init__(
            AttrMap(self.top_widget, 'frame'), AttrMap(SolidFill(), 'bg'),
            align = 'center', width = ('relative', 95),
            valign = 'middle', height = ('relative', 95),
            **kwargs
        )

class SearchBar(WidgetWrap):
    def __init__(self, **kwargs):
        self.search_text_label = Text('Textual search: ')
        self.search_text_field = Edit(wrap = 'clip')
        self.room_type_label = Text('Room type: ')
        self.room_type_field = Edit(wrap = 'clip')
        self.sentiment_label = Text('Sentiment tags: ')
        self.sentiment_field = Edit(wrap = 'clip')
        self.search_text = Columns((
            ('pack', self.search_text_label),
            ('weight', 75, LineBox(self.search_text_field, tline='', lline='', rline='')),
            ('weight', 3, Divider()),
            ('pack', self.room_type_label),
            ('weight', 30, LineBox(self.room_type_field, tline='', lline='', rline='')),
            ('weight', 3, Divider()),
            ('pack', self.sentiment_label),
            ('weight', 30, LineBox(self.sentiment_field, tline='', lline='', rline='')),
        ))

        self.search_fields_label = Text('Search fields: ')
        self.search_fields_checkboxes = Columns(FIELDS)
        self.search_button = Button(('btn', 'Go'), on_press = lambda btn: Events.SEARCH.value.notify(self.text_field.edit_text))
        self.search_fields = Columns((
            ('pack', self.search_fields_label),
            ('weight', 75, self.search_fields_checkboxes),
            ('weight', 10, Divider()),
            ('pack', self.search_button),
        ))

        self.search_bar = Filler(
            ListBox((
                self.search_text,
                self.search_fields
            )),
            height=4,
            **kwargs
        )
        
        WidgetWrap.__init__(self, self.search_bar)
    
    def keypress(self, size, key):
        if key != 'enter': return super().keypress(size, key)
        Events.SEARCH.value.notify(self.text_field.edit_text)

class SearchArea(WidgetWrap):
    def __init__(self, **kwargs):
        self.search_bar = SearchBar()
        self.result_area = ListBox((Text('Mock'),) * 10)
        self.search_area = Frame(
            header = self.search_bar,
            body = self.result_area,
            focus_part = 'header',
            **kwargs
        )
        WidgetWrap.__init__(self, self.search_area)


class Window(WidgetWrap):
    def __init__(self):
        self.description = Text(
            '''Full-text search engine for AirBnB listings with support for sentiment analysis and word2vec.\n'''
            '''Try it yourself with queries like: "Manhattan apartment with amazing skyline view", "Row house nearby Brooklyn Bridge", "Cheap room in dangerous block"'''
        )
        self.search_area = SearchArea()
        self.search_area = LineBox(self.search_area)
        self.search_area = Padding(self.search_area, width = ('relative', 90), align = 'center')
        self.inner_container = Frame(
            header = self.description,
            body = self.search_area,
            footer = Text("controls")
        )
        self.base_container = BaseContainer(self.inner_container)
        WidgetWrap.__init__(self, self.base_container)