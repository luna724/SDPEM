import os
from typing import *
from typing import Tuple, Any

from jsonutil import BuilderConfig, JsonUtilities
from modules.util import Util


class CharacterTemplate(Util):
    def __init__(self):
        bcfg = BuilderConfig()
        self.file = JsonUtilities(os.path.join(os.getcwd(), "configs/chara_template.json"))

    def load(self) -> dict:
        return self.file.read()

    def save(self, new):
        # バックアップ
        with open(os.path.join(os.getcwd(), f"logs/chara_template/{self.time_now().replace(':', '-')}-backup.json"), "w",
                  encoding="utf-8") as f:
            json.dump(self.load(), f, indent=2, ensure_ascii=False)  # type: ignore
        self.file.save(new)

    def list_characters(self):
        return self.load().keys()

    """load v3 template"""
    @staticmethod
    def load_v3(data):
        return (
            data.get("lora", ""),
            data.get("name", ""),
            data.get("prompt", ""),
            data.get("extend", "")
        )

    """Supports up: v3, v4, v5, v6"""
    def load_character_data(self, target: str) -> tuple[str, str, str, str] | tuple:
        if not target in self.list_characters():
            print(f"[FATAL]: Target characters not found ({target})")
            raise IndexError(f"target characters not found ({target})")

        chara = self.load()[target]
        version = chara[0]
        data = chara[1]
        if version in ["v3", "v4", "v5"]:
            return self.load_v3(data)
        return ()

    """$LORAなどのきゃらトリガーを変換
    from_bool が True の場合、p にリストを入れられる
    """
    def convert_all(self, p:str|List[str], target: str, from_pieces: bool = False):
