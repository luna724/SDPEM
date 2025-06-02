import io
import json
from typing import *
import os
import gradio as gr
import base64

import PIL.Image
import pyperclip

from jsonutil import JsonUtilities, BuilderConfig
from modules.image_param import ImageParamUtil
from modules.util import Util


class StaticGenerator(Util):
    def __init__(self):
        self.parser = ImageParamUtil()
        self.file = JsonUtilities(
            os.path.join(os.getcwd(), "configs/static_template.json"), BuilderConfig()
        )
        if not self.file.loadable:
            raise ValueError("Unknown Exception at initialize JsonUtilities (StaticTemplate.init)")

    def load(self) -> dict:
        return self.file.read()

    def save(self, new):
        # バックアップ
        with open(os.path.join(os.getcwd(), f"logs/static_template/{self.time_now().replace(':', '-')}-backup.json"),
                  "w",
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

    @staticmethod
    def get_default() -> dict:
        return {
            "version": 1,  # DO NOT CHANGE
            "default_key": None,
            "prompt": "",
            "negative": "",
            "original_author": None,
            "timestamp": None,
            "image_64": None,
            "has_image": False
        }

    def save_template(
            self, # 優先度: json > image > text
            param, image_param, json_path, key, overwrite, use_default_neg,
            out_as_json, no_image_saving, author
    ):
        if json_path == "Please select file.": json_path = ""
        if param == "" and image_param is None and json_path == "":
            raise gr.Error("Which one parameters needed.")
        current = self.load()

        if not json_path == "":
            # JSONからparamを読み取る
            cfg = BuilderConfig()
            cfg.required = False
            json_obj = JsonUtilities(json_path, cfg)
            if not json_obj.loadable:
                raise gr.Error("JSON File damaged or not found")
            new = json_obj.read()
            try:
                if key == "":
                    key = new["default_key"]
                if new["has_image"] and new["image_64"] is not None:
                    image = new["image_64"]
                else:
                    image = None
            except KeyError:
                image = None
        else:
            # param / image_param
            (data_obj, param_raw), _ = self.convert_from_param(param, image_param)
            new = self.get_default()
            new["default_key"] = key
            new["prompt"] = data_obj["prompt"]
            new["negative"] = data_obj["negative"]
            new["original_author"] = author.strip()
            new["raw"] = param_raw

        if use_default_neg:
            gr.Warning("Default Negatives currently unavailable")

        if image_param is not None:
            with io.BytesIO() as buffer:
                image_param.save(buffer, format="PNG")  # PNG形式で保存
                buffer.seek(0)  # バッファの先頭に戻る
                image = base64.b64encode(buffer.read()).decode("utf-8")
        else:
            image = None

        if no_image_saving:
            image = None

        if image is not None:
            new["image_64"] = image
            new["has_image"] = True

        if out_as_json:
            with open(os.path.join(
                os.getcwd(), "outputs", f"{self.time_now().replace(':', '')}-{key}.json"
            ), "w", encoding="utf-8") as f:
                json.dump(new, f, indent=2) # type: ignore
            gr.Info("Success! files saved at pem/outputs")

        else:
            if key in list(current.keys()):
                if not overwrite:
                    raise gr.Error("this display names already taken.")
            current[key] = [new]
            self.save(current)
            gr.Info("Success!")

        return gr.update()

    def load_template(self, template_key, load_image:bool = False) -> dict:
        current = self.load()
        if not template_key in current.keys():
            return {}

        template = current[template_key][0]
        prompt = template["prompt"]
        negative = template["negative"]
        original_author = template["original_author"]
        times = template["timestamp"]
        has_image = template["has_image"]
        image_b64 = template["image_64"]

        if has_image and load_image:
            decoded_image = base64.b64decode(image_b64)
            with io.BytesIO(decoded_image) as buffer:
                image = PIL.Image.open(buffer)
                image = image.copy()

        else:
            image = None

        return {
            "prompt": prompt, "negative": negative, "author": original_author,
            "times": times, "has_img": image is not None, "image": image, "raw": template["raw"]
        }

    def generate(self, template_key):
        data = self.load_template(template_key, load_image=True)
        if data == {}: raise gr.Error("Templates cannot found")

        prompt = data["prompt"]
        negative = data["negative"]
        author = data["author"]
        has_image = data["has_img"]
        image = data["image"]

        param = prompt + "\nNegative prompt: " + negative + "\n" + data["raw"]
        param_image = PIL.Image.new("1", (64, 64))
        param_image.info["parameters"] = param
        fn = self.calculate_sha256(param)

        dir = os.path.join(
            os.getcwd(), "param_images", fn + ".png"
        )
        if not os.path.exists(dir):
            param_image.save(
                dir, "PNG"
            )
            gr.Info("Images successfully created!")
        else:
            print("param image already found. skipping save")

        return prompt, negative, author, image, dir