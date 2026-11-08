# event_bus.py
from collections import defaultdict
from typing import Callable, Any

class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        print("Event bus initialized")

    def subscribe(self, event_type: type, callback: Callable):
        print(f"{callback} subscribed to event {event_type}")
        self._subscribers[event_type].append(callback)

    def emit(self, event: Any):
        print(f"emitted event {event}")
        for callback in self._subscribers[type(event)]:
            print(f"calling {callback} in response to event {event}")
            callback(event)

# Global or passed via dependency injection
EVENT_BUS = EventBus()