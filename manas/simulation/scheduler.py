from __future__ import annotations

import heapq
from itertools import count

from manas.simulation.models import SimulationEvent


class EventScheduler:
    def __init__(self) -> None:
        self._queue: list[tuple[int, int, SimulationEvent]] = []
        self._sequence = count()

    def schedule(self, event: SimulationEvent) -> None:
        heapq.heappush(self._queue, (event.day, next(self._sequence), event))

    def events_for_day(self, day: int) -> list[SimulationEvent]:
        result = []
        while self._queue and self._queue[0][0] <= day:
            _, _, event = heapq.heappop(self._queue)
            result.append(event)
        return result

    def __len__(self) -> int:
        return len(self._queue)
