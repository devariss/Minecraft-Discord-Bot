import asyncio
import discord
import json
import minecraft

from plugin import PluginServer, PluginBot, PluginResources
from typing import AsyncIterator, Final

resources: Final = PluginResources("resources\\bot.json")
bot: Final = PluginBot()
server: Final = PluginServer(resources.host, resources.port)

async def handle_channel_messages(message_event: AsyncIterator[discord.Message]):
    async for message in message_event:
        if not message.author.bot:
            message_info = json.dumps({
                "name": message.author.name,
                "channel": message.channel.name,
                "content": message.content
            })
            await server.send(f"MESSAGE {message_info}\n".encode())

async def handle_player_messages(message_event: AsyncIterator[minecraft.Message]):
    async for message in message_event:
        await bot.send_as_temp_webhook(
            resources.player_message_channel_id, 
            message.player.name, 
            message.content, 
            avatar=message.player.get_head_texture(size=(512, 512)))

async def main():
    asyncio.create_task(handle_channel_messages(bot.message_event))
    asyncio.create_task(handle_player_messages(server.message_event))
    async with asyncio.TaskGroup() as blocking_group:
        blocking_group.create_task(server.start())
        blocking_group.create_task(bot.start(resources.token))

if __name__ == "__main__":
    asyncio.run(main())