import re
from typing import *
from PIL import Image
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import io


class ImageParamUtil:
    def __init__(self):
        pass

    @staticmethod
    def extract_png_metadata(image_path_or_object):
        """
        Extract all embedded data from a PNG file.

        Args:
            image_path_or_object: Either a path to a PNG file or a PIL Image object

        Returns:
            dict: All metadata found in the PNG file
        """
        # Handle both file paths and Image objects
        if isinstance(image_path_or_object, str):
            img = Image.open(image_path_or_object)
        elif isinstance(image_path_or_object, Image.Image):
            img = image_path_or_object
        else:
            raise ValueError("Input must be a file path or PIL Image object")

        # Ensure we're dealing with a PNG
        if img.format != "PNG" and not hasattr(img, "info"):
            # If it's not a PNG but has been converted from one, try to preserve info
            if not hasattr(img, "info"):
                return {}

        metadata = {}

        # Extract standard info
        metadata["mode"] = img.mode
        metadata["size"] = img.size

        # Extract all info dictionary items
        for key, value in img.info.items():
            metadata[key] = value

        # Get raw PNG chunks
        if hasattr(img, "png") and hasattr(img.png, "chunks"):
            chunks = []
            for chunk_type, chunk_data in img.png.chunks:
                chunks.append({
                    "type": chunk_type.decode('latin-1'),
                    "data": chunk_data[:20] + b'...' if len(chunk_data) > 20 else chunk_data,
                    "length": len(chunk_data)
                })
            metadata["raw_chunks"] = chunks

        return metadata

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
