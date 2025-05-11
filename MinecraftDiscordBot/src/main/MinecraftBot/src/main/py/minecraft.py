import base64
import json
import requests

from io import BytesIO
from PIL import Image
from typing import Final

class Player:
    def __init__(self, name: str):
        self.name: Final = name
        self.uuid: Final[str] = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{name}").json()["id"]
        self.skin_url: Final[str] = json.loads(base64.b64decode(requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid}?unsigned=false").json()["properties"][0]["value"]))["textures"]["SKIN"]["url"]

    def get_head_texture(self, size: tuple[int, int] = (8, 8)) -> bytes:
        with Image.open(BytesIO(requests.get(self.skin_url).content)).crop((8, 8, 16, 16)).resize(size, resample=Image.NEAREST) as head_image:
            with BytesIO() as buffer:
                head_image.save(buffer, format="PNG")
                buffer.seek(0)
                return buffer.read()

class Message:
    def __init__(self, player: Player, content: str):
        self.player: Final = player
        self.content: Final = content