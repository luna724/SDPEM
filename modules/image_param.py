import re
from typing import *
from PIL import Image

class ImageParamUtil:
    def __init__(self):
        pass

    def replace_param(self, image: Image, param: str) -> Image:
        ##TODO: add function
        if not isinstance(image, Image.Image):
            raise ValueError("add_param are can only accept PIL.Image.Image")
        image.info["parameters"] = param
        return image

    def read_param(self, image: Image) -> str:
        param = image.info.get("parameters", None)
        if param is None:
            print(f"[WARN]: params Not found")
        return param

    def parse_param(self, param:str) -> tuple[dict, str]:
        try:
            print("[INFO]: Parsing parameters..")
            prompt_pattern = re.compile(r'^(Negative prompt): (.+?)(?=\n[A-Z][a-z]+\s|$)', re.DOTALL | re.MULTILINE)

            # プロンプトの解析
            neg = prompt_pattern.findall(param)
            if len(neg) < 1:
                print(f"[FATAL]: Parameter parsing failed at Negative (IndexError) (param: {param})")
                return {}, ""

            negative = neg[0][1]
            print("[INFO]: parsed Negative: ", negative)
            prompt = re.sub(
                r"(\nNegative prompt:.+)", "", param.split(negative)[0], 1
            )
            return_obj = {
                "prompt": prompt,
                "negative": negative
            }
            print("[INFO]: parsed Prompt: ", prompt)

            other_param_text = f"{negative}".join(param.split(negative)[1:])
            parameter_pattern = re.compile(r'([A-Za-z0-9_\s]+): (?:(?:"([^"]+)")|([^,]+)),?')

            # パラメータの抽出
            parameters = parameter_pattern.findall(other_param_text)
            for parameter in parameters:
                key = parameter[0].strip()
                value = parameter[1] if parameter[1] else parameter[2]
                value = value.strip()
                return_obj[key] = value
            return return_obj, other_param_text
        except IndexError as e:
            raise IndexError("Failed parsing parameters.")
