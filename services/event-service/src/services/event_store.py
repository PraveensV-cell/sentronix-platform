from __future__ import annotations

from src.schemas.event import EventResponse


class EventStore:
    """
    In-memory event storage.

    Temporary storage for Phase 4.
    Will be replaced by database repository in Phase 5.
    """

    def __init__(self):
        self._events: dict[str, EventResponse] = {}

    def add(
        self,
        event: EventResponse,
    ) -> None:
        """
        Store an event.
        """

        self._events[event.event_id] = event

    def get_all(
        self,
    ) -> list[EventResponse]:
        """
        Return all stored events.
        """

        return list(
            self._events.values(),
        )

    def get(
        self,
        event_id: str,
    ) -> EventResponse | None:
        """
        Get event by id.
        """

        return self._events.get(
            event_id,
        )

    def delete(
        self,
        event_id: str,
    ) -> bool:
        """
        Delete event by id.
        """

        if event_id in self._events:
            del self._events[event_id]

            return True

        return False

    def clear(
        self,
    ) -> None:
        """
        Remove all events.
        """

        self._events.clear()

    def count(
        self,
    ) -> int:
        """
        Return stored event count.
        """

        return len(
            self._events,
        )
