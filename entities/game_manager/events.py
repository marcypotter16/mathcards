# event_bus.py
from collections import defaultdict
from typing import Callable, Any

from entities.printer import Printer

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        # Printer.print("Event bus initialized")
        print("Event bus initialized")

    def subscribe(self, event_type: type, callback: Callable):
        # Printer.print(f"{callback} subscribed to event {event_type}")
        print(f"\n{callback} subscribed to event {event_type}")
        self._subscribers[event_type].append(callback)

    def emit(self, event: Any):
        # Printer.print(f"emitted event {event}")
        print(f"\nemitted event {event}")
        for callback in self._subscribers[type(event)]:
            # Printer.print(f"calling {callback} in response to event {event}")
            print(f"\ncalling {callback} in response to event {event}")
            callback(event)

# Global or passed via dependency injection
EVENT_BUS = EventBus()