import asyncio

from abc import ABC as abstract
from abc import abstractmethod
from typing import Any, Awaitable, AsyncIterator, AsyncIterable, Generator

class AAsyncIterator[T](Awaitable[T], AsyncIterator[T]):
    pass

class Signalable[T](abstract):
    @abstractmethod
    async def signal(self, payload: T):
        pass

class Event[T](AAsyncIterator[T], AsyncIterable[T], Signalable[T]):
    """Higher level Event primitive that delivers a payload. 

    (Not thread safe!)"""

    def __init__(self):
        self._payload: T = None
        self._signal_event = asyncio.Event()

    def __await__(self) -> Generator[Any, None, T]:
        yield from asyncio.sleep(0).__await__()
        yield from self._signal_event.wait().__await__()
        return self._payload

    def __aiter__(self):
        return self
    
    async def __anext__(self) -> T:
        return await self

    async def signal(self, payload: T):
        """Delivers payload to all awaiting tasks. Skips one event loop cycle."""

        self._payload = payload
        self._signal_event.set()
        await asyncio.sleep(0)
        self._signal_event.clear()