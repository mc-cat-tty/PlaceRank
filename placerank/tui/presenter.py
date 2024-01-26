"""
This module offers a loose presenter (part of MVP) implementation. In this specific implementation
the presenter receives TUI events - actually, not all events, just those that affect the model, since
view-related events are "self contained" inside the UI - through the event broker. It then reroutes
the update event to the model (IR stack), which in turn does some computation: it usually performs
a new query; but the update can also be a change of `IRModel`.
The new content is afterwards sent to the view through the broker, once again.
From a practical point of view, `Presenter` is a singleton, of which the view is unaware, while the
model being injected as a dependency in it. 
"""
from __future__ import annotations
from placerank.models import IRModel
from placerank.tui.events import Event, Events, Observer
from placerank.views import QueryLogicView
from typing import Any


class Presenter:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, model: IRModel):
        self._model = model
        self.search_observser = Observer(self.search_query_update, [Events.SEARCH_QUERY_UPDATE.value])
    
    def search_query_update(self, event: Event, query: QueryLogicView) -> Any:
        Events.SEARCH_RESULTS_UPDATE.value.notify([f'FOUND {query.textual_query}',] * 10)
