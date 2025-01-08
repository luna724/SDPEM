import os
import re
from typing import *
import gradio as gr
import json

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

    @staticmethod
    def get_base_v3():
        return {
            "lora": "",
            "name": "",
            "prompt": "",
            "extend": ""
        }

    """load v6 template"""
    @staticmethod
    def load_v6(data):
        return (
            data.get("lora", ""),
            data.get("name", ""),
            data.get("prompt", ""),
            data.get("default-weight", ""),
            data.get("chara-types", {})
        )

    @staticmethod
    def get_base_v6():
        return {
            "lora": "LoRAトリガー、",
            "name": "$NAME プレースホルダー、",
            "prompt": "$PROMOT プレースホルダー、",
            "default-weight": "LoRAのデフォルトウェイト、",
            "chara-types": {
                    # "type": "特定スタイル",
                },
            "isXL": False # SDXL
            }

    @staticmethod
    def check_lora_trigger(lora_trigger) -> bool:
        pattern = re.compile(
            r"^<lora:.*:.*>$", re.IGNORECASE
        )
        matched = pattern.findall(lora_trigger.strip().lower())
        if len(matched) > 0: return True
        return False

    def new_chara_v3(
            self, version: Literal["v3 Legacy", "v6"],
            key, lora, name, prompt, overwrite
    ):
        current = self.load()
        current_keys = list(current.keys())

        if key in current_keys:
            if not overwrite:
                raise gr.Error("This display names already taken.")
        if not self.check_lora_trigger(lora):
            raise gr.Error("LoRA Trigger validate check failed.")

        if version == "v3 Legacy":
            gr.Info("v3 Legacy is deprecated. Please use v6 instead.")

        new = None
        if version == "v3":
            new = self.get_base_v3()
        elif version == "v6":
            raise gr.Error("V6 called in v3 function")

        # 全体変数
        new["lora"] = lora
        new["name"] = name
        new["prompt"] = prompt
        current[key] = [version, new]
        self.save(current)
        gr.Info("Success!")

    def new_chara_v6(
            self, version: Literal["v3 Legacy", "v6"],
            key: str, lora: str, name: str, prompt: str, default_weight: str,
            chara_types: dict, overwrite: bool
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
            return self.load_v6(data)
        return ()

    """$LORAなどのきゃらトリガーを変換
    from_pieces が True の場合、p にリストを入れられる
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


    def template_updater(self, update_v3: bool = False):
        current_template = self.load()
        for key in current_template.keys():
            version = current_template[key][0]
            if version == "v6" or (not update_v3 and version == "v3"):
                continue

            data = current_template[key][1]
            new_data = self.get_base_v6()

            if version in ["v3", "v4", "v5"]:
                new_data["lora"] = data["lora"]
                new_data["name"] = data["name"]
                new_data["prompt"] = data["prompt"]
                new_data["default-weight"] = "1.0"
                new_data["chara-types"] = {"default": data["extend"]} if data["extend"] != "" else {}

            if version == "v5":
                # lv を chara-types に移動
                lora_variables_status = data.get("lora-variables", [[False, False],[]])
                new_data["chara-types"].update(
                    {
                        v[0]: v[1]
                        for k, v in zip(
                        lora_variables_status[0], lora_variables_status[1]
                    )
                        if k
                        if v[0] != ""
                        if v[0] != "default"
                    }
                )

            ## TODO: isXLの検出処理
            current_template[key] = ["v6", new_data]
        self.save(current_template)

