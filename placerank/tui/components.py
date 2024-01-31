from __future__ import annotations
import functools
from urwid import *
from placerank.views import SearchFields, ResultView, QueryView, DocumentView, ReviewView
from placerank.tui.events import *
from placerank.tui.presenter import *
from enum import Enum, auto

PALETTE = (
    ('fg', 'black', 'light gray'),
    ('bg', 'black', 'dark magenta'),
    ('title', 'light magenta', 'light gray'),
    ('frame', 'white', 'light gray'),
    ('btn', 'light magenta', 'light gray'),
    ('reversed', 'white', 'dark magenta', 'standout'),  # Improper use. Remove this record for real inverted color focused items
    ('link', 'black, underline', 'light gray')
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
        self.room_type_label = Text('Room-type filter: ')
        self.room_type_field = Edit(wrap = 'clip')
        self.sentiment_label = Text('Sentiment tags: ')
        self.sentiment_field = Edit(wrap = 'clip')
        self.search_text = Columns((
            ('pack', self.search_text_label),
            ('weight', 30, LineBox(self.search_text_field, tline='', lline='', rline='')),
            ('weight', 3, Divider()),
            ('pack', Pile((self.room_type_label, Text('[Private|Shared|Hotel|Entire] ')))),
            ('weight', 30, LineBox(self.room_type_field, tline='', lline='', rline='')),
            ('weight', 3, Divider()),
            ('pack', self.sentiment_label),
            ('weight', 30, LineBox(self.sentiment_field, tline='', lline='', rline='')),
        ))

        self.search_fields_label = Text('Search fields: ')
        self.search_fields_checkboxes = Columns(self.checkboxes)
        self.search_button = Button(('btn', 'Go'), on_press = lambda _: self._search_listener())
        self.search_fields = Columns((
            ('pack', self.search_fields_label),
            ('weight', 75, self.search_fields_checkboxes),
            ('weight', 10, Divider()),
            ('pack', AttrMap(self.search_button, None, focus_map='reversed')),
        ))

        self.dym_suggestion = Text(' ')
        self.expanded_suggestion = Text(' ')
        self.autoexpansion = CheckBox('', False)

        self.correction_line = Columns((
            ('pack', Text('Did you mean ')),
            ('pack', AttrMap(self.dym_suggestion, 'link', 'reversed')),
            ('pack', Text('?'))
        ))

        self.expansion_line =  Columns((
            ('pack', Text('You may want to try "')),
            ('pack', self.expanded_suggestion),
            ('pack', Text('" to increase recall'))
        ))

        self.enable_expansion = Columns((
            ('pack', Text('This is just a propostal. Enable autoexpansion? ')),
            (('pack', self.autoexpansion))
        ))

        self.new_suggestion = Observer(self._update_suggestion, [Events.DID_YOU_MEAN.value, Events.EXPANDED_ALTERNATIVE.value])
        connect_signal(self.autoexpansion, 'change', lambda _, state: self._autoexpansion_change(state))

        self.search_bar = Filler(
            ListBox((
                self.search_text,
                Divider(),
                self.search_fields,
                Divider(),
                Filler(self.correction_line),
                Filler(self.expansion_line),
                Filler(self.enable_expansion)
            )),
            height=9,
            **kwargs
        )


        WidgetWrap.__init__(self, self.search_bar)

    def _autoexpansion_change(self, state):
        Events.AUTOEXPANSION_STATE_CHANGE.value.notify(state)
        self._search_listener()

    def _update_suggestion(self, e: Event, suggestion: str):
        if e == Events.DID_YOU_MEAN.value:
            def active_mouse_event(size, event, button, col, row, focus):
                if event != 'mouse release':
                    return super(type(self.dym_suggestion), self.dym_suggestion).mouse_event(size, event, button, col, row, focus)
                self.search_text_field.set_edit_text(self.dym_suggestion.get_text()[0])
                self._search_listener()
            
            def inactive_mouse_event(size, event, button, col, row, focus):
                return super(type(self.dym_suggestion), self.dym_suggestion).mouse_event(size, event, button, col, row, focus)
            
            if suggestion:
                self.dym_suggestion.set_text(suggestion)
                self.dym_suggestion.mouse_event = active_mouse_event
            else:
                self.dym_suggestion.set_text(' ')
                self.dym_suggestion.mouse_event = inactive_mouse_event

        elif e == Events.EXPANDED_ALTERNATIVE.value:
            self.expanded_suggestion.set_text(suggestion)

    def _get_checkboxes_state(self) -> SearchFields:
        return functools.reduce(
            lambda x, y: x | y,
            (SearchFields[c.label] for c in self.checkboxes if c.state),
            SearchFields(0)
        )

    def _search_listener(self) -> None:
        Events.SEARCH_QUERY_UPDATE.value.notify(
            QueryView(
                self.search_text_field.edit_text,
                self._get_checkboxes_state(),
                self.room_type_field.edit_text,
                self.sentiment_field.edit_text
            )
        )

    def keypress(self, size, key):
        if key != 'enter': return super().keypress(size, key)
        self._search_listener()

class ResultCard(WidgetWrap):
    def __init__(self, result: ResultView, **kwargs):
        self.result = result
        self.card = Filler(
            AttrMap(
                cols := Columns((
                    (30, Text(str(result.id))),
                    Text(str(result.name)),
                    Text(str(result.room_type)),
                )),
                None, focus_map='reversed'
            ),
            **kwargs
        )
        self.cols = cols
        WidgetWrap.__init__(self, self.card)

    def selectable(self):
        return True

    def mouse_event(self, size, event, button, col, row, focus):
        if event != 'mouse press': return super().mouse_event(size, event, button, col, row, focus)
        Events.OPEN_RESULT_REQUEST.value.notify(self.result.id)

    def keypress(self, size, key):
        if key != 'enter': return super().keypress(size, key)
        Events.OPEN_RESULT_REQUEST.value.notify(self.result.id)



class SearchArea(WidgetWrap):
    def __init__(self, **kwargs):
        self.search_bar = SearchBar()
        self.results = SimpleFocusListWalker([])
        self.result_area = LineBox(ListBox(self.results), 'Results')
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

    def _results_listener(self, event: Event, results: List[ResultView], total_res: int) -> None:
        self.result_area.set_title(f'Showing top {len(results)} results. {total_res} total hits.')
        self.results.clear()
        self.results.extend(SimpleFocusListWalker(map(ResultCard, results)))
        self.results.set_focus(0)

class Controls(WidgetWrap):
    def __init__(self, **kwargs):
        self.advanced = Button('Advanced', on_press = self.btn_press)
        self.help = Button('Help', on_press = self.btn_press)
        self.exit = Button('Exit', on_press = self.btn_press)
        self.btns = (self.advanced, self.help, self.exit)
        self.controls = Columns((
                ('weight', 35, Divider()),
                # ('weight', 10, AttrMap(self.advanced, None, focus_map='reversed')),
                # ('weight', 6, Divider()),
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
        if btn == self.advanced: return Events.ADVANCED_SCREEN.value.notify()
        if btn == self.help: return Events.HELP_SCREEN.value.notify()
        if btn == self.exit: return Events.EXIT.value.notify()

class Window(WidgetWrap):
    class Page(Enum): MAIN = auto(); HELP = auto(); ADVANCED = auto()

    def __init__(self, help_txt: str):
        # STATE
        self.help_txt = help_txt
        self.main_description_txt = (
            '''Full-text search engine for AirBnB listings with support for sentiment tagging and contextual query expansion.\n'''
            '''Try it yourself with queries like: "Manhattan apatment" (not the missing "r"), "Modern shared room near Cornell", "Row house by the Hudson"\n'''
            '''Experiment with sentiment analysis by submitting queries like "long stay" with tags like "disappointment" and "disgust" (space-separated).\n'''
            '''Check <Help> page for more details about the available classes.\n'''
        )
        self.current_page: int | self.Page = self.Page.MAIN

        # COMPONENTS
        self.description = Text(self.main_description_txt)
        self.search_area = SearchArea()
        self.search_area = LineBox(self.search_area)
        self.search_area = Padding(self.search_area, width = ('relative', 90), align = 'center')
        self.content_area = WidgetPlaceholder(self.search_area)
        self.controls = Controls()
        self.inner_container = Frame(
            header = self.description,
            body = self.content_area,
            footer = self.controls
        )
        self.base_container = BaseContainer(self.inner_container)

        # CALLBACKS
        self.inner_container_focus_change = Observer(
            lambda e: self.inner_container.set_focus('footer' if e == Events.MOVE_FOCUS_TO_CONTROLS.value else 'body'),
            [Events.MOVE_FOCUS_TO_CONTROLS.value, Events.MOVE_FOCUS_TO_SEARCH.value]
        )
        self.help_page_request = Observer(self._open_help_page, [Events.HELP_SCREEN.value])
        self.advanced_page_request = Observer(self._open_advanced_page, [Events.ADVANCED_SCREEN.value])
        self.open_result= Observer(self._open_result, [Events.OPEN_RESULT.value])
        self.exit_callback = Observer(self._exit_callback, [Events.EXIT.value])

        WidgetWrap.__init__(self, self.base_container)

    def _open_help_page(self, event: Event):
        if self.current_page == self.Page.HELP: return

        self.content_area.original_widget = Padding(
            LineBox(Text(self.help_txt)),
            width = ('relative', 90), align = 'center'
        )

        self.description.set_text('HELP PAGE')
        self.current_page = self.Page.HELP
        Events.MOVE_FOCUS_TO_SEARCH.value.unregister_observer(self.inner_container_focus_change)

    def _open_advanced_page(self, event: Event):
        if self.current_page == self.Page.ADVANCED: return

        self.content_area.original_widget = Padding(
            LineBox(Text('Advanced')),
            width = ('relative', 90), align = 'center'
        )
        self.description.set_text('ADVANCED PAGE')
        self.current_page = self.Page.ADVANCED
        Events.MOVE_FOCUS_TO_SEARCH.value.unregister_observer(self.inner_container_focus_change)

    def _open_result(self, event: Event, doc: DocumentView, reviews: List[ReviewView]):
        if self.current_page == doc.id: return

        result_body = Pile(
            (Text([('title', f'{key.upper()}: '), val]) for key, val in zip(doc._fields, doc))
        )

        if reviews:
            reviews_widget = Pile(
                (Text([('title', r.date.strftime('%d/%m/%Y ')), r.comments[:1000]]) for r in reviews[:3])
            )
        else:
            reviews_widget = Text('NO REVIEW')

        reviews_body = LineBox(
            reviews_widget,
            title = 'REVIEWS',
            title_attr = 'title'
        )

        self.content_area.original_widget = Padding(
            LineBox(
                Pile((result_body, Divider(), reviews_body))
            ),
            width = ('relative', 90), align = 'center'
        )
        self.current_page = 1
        self.inner_container.set_focus('footer')
        self.controls.controls.set_focus(3)
        Events.MOVE_FOCUS_TO_SEARCH.value.unregister_observer(self.inner_container_focus_change)

    def _exit_callback(self, event: Event):
        if self.current_page == self.Page.MAIN:
            raise ExitMainLoop()

        Events.MOVE_FOCUS_TO_SEARCH.value.register_observer(self.inner_container_focus_change)
        self.description.set_text(self.main_description_txt)
        self.content_area.original_widget = self.search_area
        self.current_page = self.Page.MAIN