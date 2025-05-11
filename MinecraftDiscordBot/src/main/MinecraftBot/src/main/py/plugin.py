import asyncio
import discord
import json

from asyncio import StreamWriter, StreamReader
from concurrency import AAsyncIterator, Event
from discord_extensions import Bot
from minecraft import Message, Player
from typing import Any, Final, final, Optional

class PluginServer:
    def __init__(self, host: str, port: int):
        self.host: Final = host
        self.port: Final = port
        self._message_event: Final = Event[Message]()
        self._started: bool = False
        self._writers: set[StreamWriter] = set()

    @final
    @property
    def message_event(self) -> AAsyncIterator[Message]:
        return self._message_event

    async def start(self):
        async def on_connect(client_in: StreamReader, client_out: StreamWriter):
            print("Client connected.")
            self._writers.add(client_out)
            try:
                async for in_data in client_in:
                    data = in_data.strip().decode()
                    sep_index = data.find(" ")
                    request = data[:sep_index]
                    obj = json.loads(data[sep_index + 1:])
                    await self._handle_request(request, obj)
            except Exception as e:
                self._writers.remove(client_out)
                print(f"Client disconnected.\n{type(e).__name__}: {e}")
        if not self._started:
            async with await asyncio.start_server(on_connect, self.host, self.port) as server:
                self._started = True
                await server.serve_forever()

    async def send(self, data: bytes):
        for writer in self._writers:
            writer.write(data)
            await writer.drain()

    async def _handle_request(self, request: str, obj: Any):
        match request:
            case "MESSAGE":
                await self._message_event.signal(Message(Player(obj["name"]), obj["content"]))
            case _:
                raise Exception("Undefined incoming request from client.")

class PluginBot(Bot):
    @property
    def intents(self) -> discord.Intents:
        intents = discord.Intents.default()
        intents.message_content = True
        return intents
    
    async def send_as_temp_webhook(self, channel_id: int, name: str, content: str, avatar: Optional[bytes] = None):
        webhook: discord.Webhook = await self.get_channel(channel_id).create_webhook(name=name, avatar=avatar)
        await webhook.send(content)
        await webhook.delete()
    
class PluginResources:
    def __init__(self, path: str):
        with open(path) as resources_raw:
            resources = json.loads(resources_raw.read())
        self.token: Final[str] = resources["token"]
        self.host: Final[str] = resources["host"]
        self.port: Final[int] = resources["port"]
        self.guild_id: Final[int] = resources["guild_id"]
        self.player_message_channel_id: Final[int] = resources["player_message_channel_id"]