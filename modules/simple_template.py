import os
from typing import *
import gradio as gr
import PIL.Image
import json

from jsonutil import BuilderConfig, JsonUtilities
from modules.character_exchanger import CharacterExchanger
from modules.image_param import ImageParamUtil
from modules.util import Util


class SimpleTemplate(Util):
    def  __init__(self):
        self.parser = ImageParamUtil()
        self.ce = CharacterExchanger()

        # Jsonインスタンス
        bcfg = BuilderConfig()
        self.file = JsonUtilities("./configs/simple_template.json", bcfg)
        if not self.file.loadable:
            raise ValueError("Unknown Exception at initialize JsonUtilities (SimpleTemplate.init)")

        # base
        self.base_json = {
            "version": 1,
            "prompt": "",
            "negative": "",
            "others": None,
            "raw": ""
        }

    """SimpleTemplateの読み込み"""
    def load(self) -> dict:
        return self.file.read()

    """SimpleTemplateの保存"""
    def save(self, new):
        # バックアップ
        with open(os.path.join(os.getcwd(), f"logs/simple_template/{self.time_now().replace(':', '-')}-backup.json"), "w",
                  encoding="utf-8") as f:
            json.dump(self.load(), f, indent=2, ensure_ascii=False)  # type: ignore
        self.file.save(new)

    """
    どちらも送られた場合、image_paramを優先する
    """
    def convert_from_param(self, param, image_param: PIL.Image.Image | None = None):
        if image_param is None:
            return self.parser.parse_param(param), param
        else:
            param = self.parser.read_param(image_param)
            return self.parser.parse_param(param), param

    """Define/from Param 用の保存関数"""
    def tunnel_for_ui_from_param(
            self, param, image_param, key, overwrite, auto_convert, no_negative, include_extension
    ):
        if param == "" and image_param is None:
            raise gr.Error("which one parameters needed")

        data_obj, param_raw = self.convert_from_param(param, image_param)
        print("[INFO]: Parsed obj: ", data_obj)
        current = self.load()
        current_keys = current.keys()

        if key in current_keys:
            if not overwrite:
                raise gr.Error("this display names already taken.")
            gr.Warning("old display name found. (will overwritten)")

        # プロンプトを変換
        prompt = data_obj["prompt"]
        if auto_convert:
            prompt = self.ce.exchange_v4(["lora", "name", "prompts"], prompt, None, for_template=True)[0]

        negative = data_obj["negative"]
        if no_negative:
            negative = ""

        ## TODO: LoRADatabaseProcessor のようなメゾットに切り替える
        new = self.base_json
        new["prompt"] = prompt
        new["negative"] = negative
        new["others"] = data_obj
        new["raw"] = param_raw
        current[key] = [new]
        self.save(current)

        gr.Info("Success!")
        return gr.update()

    """テンプレートのキーを返す"""
    def list_templates(self):
        return self.file.read().keys()