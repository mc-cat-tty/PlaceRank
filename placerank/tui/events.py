"""
This module makes use of the Observer design pattern to dispatch events (also called subjects) to all subscribed 
observers. Each event holds a list of subscribers - i.e. the observers - that will be notified when the event occurs. 
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Any
from weakref import WeakSet
from enum import Enum

class Broker(Enum):
    """
    Event broker is the aggregator under which all the events are stored
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance
    

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
    def __init__(self, notification_callback: Callable[[Event, Any, Any], None]):
        self.__notify_event = notification_callback
    
    @abstractmethod
    def notify_event(self, caller: Event, *args, **kwargs):
        return self.__notify_event(caller, *args, **kwargs)