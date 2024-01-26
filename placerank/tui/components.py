from __future__ import annotations
import functools
from urwid import *
from placerank.views import SearchFields
from placerank.tui.events import *
from placerank.tui.presenter import *
from functools import reduce

PALETTE = (
    ('fg', 'black', 'light gray'),
    ('bg', 'black', 'dark magenta'),
    ('title', 'light magenta', 'light gray'),
    ('frame', 'white', 'light gray'),
    ('btn', 'light magenta', 'light gray')
)

FIELDS = (f.name for f in SearchFields)

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
        self.checkboxes: List[CheckBox] = [CheckBox(f, True) for f in FIELDS]
        
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
        self.search_fields_checkboxes = Columns(self.checkboxes)
        self.search_button = Button(('btn', 'Go'), on_press = lambda btn: self._search_listener())
        self.search_fields = Columns((
            ('pack', self.search_fields_label),
            ('weight', 75, self.search_fields_checkboxes),
            ('weight', 10, Divider()),
            ('pack', AttrMap(self.search_button, None, focus_map='reversed')),
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
    
    def _get_checkboxes_state(self) -> SearchFields:
        return functools.reduce(
            lambda x, y: x | y,
            (SearchFields[c.label] for c in self.checkboxes if c.state)
        )

    def _search_listener(self) -> None:
        Events.SEARCH_QUERY_UPDATE.value.notify(
            QueryLogicView(
                self.search_text_field.edit_text,
                self._get_checkboxes_state(),
                self.room_type_field.edit_text,
                self.sentiment_field.edit_text
            )
        )

    def keypress(self, size, key):
        if key != 'enter': return super().keypress(size, key)
        self._search_listener()

class SearchArea(WidgetWrap):
    def __init__(self, **kwargs):
        self.search_bar = SearchBar()
        self.results = SimpleFocusListWalker([])
        self.result_area = ListBox(self.results)
        self.search_area = Pile(
            (('pack', self.search_bar), self.result_area),
            focus_item = self.search_bar,
            **kwargs
        )

        self.search_results_update = Observer(self._results_listener, [Events.SEARCH_RESULTS_UPDATE.value])

        WidgetWrap.__init__(self, self.search_area)
    
    def keypress(self, size, key):
        if key != 'tab': return super().keypress(size, key)
        Events.MOVE_FOCUS_TO_CONTROLS.value.notify()
    
    def _results_listener(self, event: Event, results: List[str]) -> None:
        self.results.clear()
        self.results.extend(SimpleFocusListWalker(map(Text, results)))

class Controls(WidgetWrap):
    def __init__(self, **kwargs):
        self.advanced = Button('Advanced', on_press = self.btn_press)
        self.help = Button('Help', on_press = self.btn_press)
        self.exit = Button('Exit', on_press = self.btn_press)
        self.btns = (self.advanced, self.help, self.exit)
        self.controls = Columns((
                ('weight', 35, Divider()),
                ('weight', 10, AttrMap(self.advanced, None, focus_map='reversed')),
                ('weight', 6, Divider()),
                ('weight', 10, AttrMap(self.help, None, focus_map='reversed')),
                ('weight', 6, Divider()),
                ('weight', 10, AttrMap(self.exit, None, focus_map='reversed')),
                ('weight', 35, Divider()),
        ))
        WidgetWrap.__init__(self, Filler(self.controls, **kwargs))
    
    def keypress(self, size, key):
        if key != 'tab': return super().keypress(size, key)
        Events.MOVE_FOCUS_TO_SEARCH.value.notify()
    
    def btn_press(self, btn):
        if btn == self.advanced: Events.ADVANCED_SCREEN.value.notify()
        if btn == self.help: Events.HELP_SCREEN.value.notify()
        if btn == self.exit: raise ExitMainLoop()

class Window(WidgetWrap):
    def __init__(self):
        self.description = Text(
            '''Full-text search engine for AirBnB listings with support for sentiment analysis and word2vec.\n'''
            '''Try it yourself with queries like: "Manhattan apartment with amazing skyline view", "Row house nearby Brooklyn Bridge", "Cheap room in dangerous block"'''
        )
        self.search_area = SearchArea()
        self.search_area = LineBox(self.search_area)
        self.search_area = Padding(self.search_area, width = ('relative', 90), align = 'center')
        self.controls = Controls()
        self.inner_container = Frame(
            header = self.description,
            body = self.search_area,
            footer = self.controls
        )
        self.base_container = BaseContainer(self.inner_container)
        
        self.inner_container_focus_change = Observer(
            lambda e: self.inner_container.set_focus('footer' if e == Events.MOVE_FOCUS_TO_CONTROLS.value else 'body'),
            [Events.MOVE_FOCUS_TO_CONTROLS.value, Events.MOVE_FOCUS_TO_SEARCH.value]
        )

        WidgetWrap.__init__(self, self.base_container)
