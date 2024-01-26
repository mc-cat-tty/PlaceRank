"""
This module makes use of the Observer design pattern to dispatch events (also called subjects) to all subscribed 
observers. Each event holds a list of subscribers - i.e. the observers - that will be notified when the event occurs. 
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Any, List
from weakref import WeakSet
from enum import Enum


class Event:
    def __init__(self):
        self.observers = WeakSet()
    
    def register_observer(self, observer: Observer) -> None:
        """
        Take into account that a weak reference of the passed observer is registered
        in order to avoid the well-known and well-addressed lapsed listener problem.
        """
        self.observers.add(observer)
    
    def unregister_observer(self, observer: Observer) -> None:
        if observer and observer in self.observers:
            self.observers.remove(observer)
    
    def notify(self, *args, **kwargs) -> None:
        """
        The source event is passed to the callback
        to disambiguate between notification reasons
        """
        for o in self.observers: o.notify_event(self, *args, **kwargs)


class Observer(ABC):
    def __init__(self, notification_callback: Callable[[Event, Any, Any], Any], event_list: List[Event] = []):
        self.__notify_event = notification_callback
        if event_list:
            for e in event_list: e.register_observer(self)
    
    def notify_event(self, caller: Event, *args, **kwargs) -> Any:
        return self.__notify_event(caller, *args, **kwargs)


class Events(Enum):
    """
    `Events` is the aggregator under which all the events are stored
    and can be retrieved with the following syntax: `Events.NAME.value`
    """
    SEARCH_QUERY_UPDATE = Event()  # Observers must listen for (event, query_view)
    SEARCH_RESULTS_UPDATE = Event()  # observers must listen for (event, search_results)
    OPEN_RESULT_REQUEST = Event()  # Observers must listen for (event, doc_id)
    OPEN_RESULT = Event()  # Observers must listern for (event, document_view)

    MOVE_FOCUS_TO_CONTROLS = Event()  # Self-explanatory. Listen for (event,)
    MOVE_FOCUS_TO_SEARCH = Event()  # Self-explanatory. Listen for (event,)
    
    ADVANCED_SCREEN = Event()  # Self-explanatory. Listen for (event,)
    HELP_SCREEN = Event()  # Self-explanatory. Listen for (event,)
    EXIT = Event()  # Self-explanatory. Listen for (event,)