import os
import re
from typing import *
from typing import Tuple, Any

from jsonutil import BuilderConfig, JsonUtilities
from modules.util import Util


class CharacterTemplate(Util):
    def __init__(self):
        bcfg = BuilderConfig()
        self.file = JsonUtilities(os.path.join(os.getcwd(), "configs/chara_template.json"))

        # 変数
        self.triggers = ["$lora", "$name", "$prompt", "$extend", "$charadef"]

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

    def new_chara(
            self,
            key, lora, name, prompt, default, overwrite
    ):
        return

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
        elif version in ["v6"]:
            return ()
        return ()

    """$LORAなどのきゃらトリガーを変換
    from_bool が True の場合、p にリストを入れられる
    """
    def convert_all(self, prompts:str|List[str], target: str, lora_weights: str, from_pieces: bool = False):
        if not from_pieces and isinstance(prompts, str):
            prompts = [
                x.strip()
                for x in prompts.split(",")
            ]
        lora, name, prompt, default = self.load_character_data(target)

        via = []
        for p in prompts:
            p = p.strip()
            if not p.lower() in self.triggers:
                via.append(p)
                continue

            if p.lower() == "$lora":
                print(f"[DEV]: $LORA Triggered (p = {p}, lora = {lora}, lora_weights = {lora_weights})")
                match = re.match(r"^<lora:.*?:(.*?)>$", lora.strip())
                if match:  # マッチが成功した場合のみ処理
                    captured_value = match.group(1)  # キャプチャグループから値を取得
                    replaced_p = lora.replace(
                            captured_value, lora_weights
                        )
                    via.append(
                        replaced_p
                    )
                else:
                    print(f"[FATAL]: $LoRA Detection Failed. $LoRA prompt will be deleted")
            elif p.lower() == "$name":
                via.append(name)
            elif p.lower() == "$prompt":
                via.append(prompt)
            elif p.lower() in ["$extend", "$charadef"]:
                via.append(default)
        return ", ".join(via).strip(",")
