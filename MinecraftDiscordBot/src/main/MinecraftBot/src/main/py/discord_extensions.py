import discord

from abc import ABC as abstract
from concurrency import Event, AAsyncIterator
from discord import Message
from typing import final, Final

class Bot(abstract, discord.Client):
    """Async event based implementation of a discord client."""

    def __init__(self):
        super().__init__(intents=self.intents)
        self._message_event: Final = Event[Message]()
        self._ready_event: Final = Event[Bot]()

    @final
    @property
    def message_event(self) -> AAsyncIterator[Message]:
        return self._message_event
    
    @final
    @property
    def ready_event(self):
        return self._ready_event

    @property
    def intents(self) -> discord.Intents:
        return discord.Intents.default()

    async def on_ready(self):
        await self._ready_event.signal(self)
    
    async def on_message(self, message: Message):
        await self._message_event.signal(message)