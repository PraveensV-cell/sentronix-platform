from src.schemas.event import EventResponse


class EventStore:
    def __init__(self):

        self._events: dict[str, EventResponse] = {}

    def add(
        self,
        event: EventResponse,
    ) -> None:

        self._events[event.event_id] = event

    def get_all(
        self,
    ) -> list[EventResponse]:

        return list(self._events.values())

    def get(
        self,
        event_id: str,
    ) -> EventResponse | None:

        return self._events.get(event_id)

    def delete(
        self,
        event_id: str,
    ) -> bool:

        if event_id in self._events:
            del self._events[event_id]

            return True

        return False

    def clear(self):

        self._events.clear()
