import base64
import binascii
import os
from io import BytesIO
from typing import Optional

import discord
from PIL import Image


class ImageUtil:
    def __init__(self, i: Image.Image = None):
        self.image: Optional[Image.Image] = i

    def put(self, image: Image.Image):
        self.image = image

    def get(self) -> Optional[Image.Image]:
        return self.image

    def absolute_get(self) -> Image.Image:
        if self.image is None:
            raise ValueError("Image isn't set")
        return self.image

    def clear(self):
        self.image = None

    def __bool__(self):
        return self.image is not None

    def load(self, i: str | bytes | BytesIO | os.PathLike) -> Image.Image:
        """
        画像を読み込む
        """
        if isinstance(i, str) or isinstance(i, os.PathLike):
            if os.path.exists(i):
                self.image = Image.open(i)
            elif isinstance(i, str):
                self.image = self.from_base64(i, safe=True)
                if self.image is None:
                    raise ValueError("ImageUtil.load: invalid base64 string (or str Path)")
            else:
                raise FileNotFoundError("ImageUtil.load: invalid path")

        elif isinstance(i, bytes) or isinstance(i, BytesIO):
            self.image = self.from_buffer(i)

        else:
            raise TypeError("ImageUtil.load: invalid type")

        return self.image


    def to_deepbooru(self, threshold: float, *, image: Image.Image = None) -> dict:
        """
        Deepbooruでタグ化する
        """
        from modules.models import deepbooru
        image = image if image is not None else self.absolute_get()

        return deepbooru.default.interrogate(
            image, threshold
        )


    def to_base64(self, *, image: Image.Image = None) -> str:
        """
        画像をbase64エンコードする
        """
        image = image if image is not None else self.absolute_get()
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")


    def from_base64(self, base64_str: str, safe: bool = False) -> Image.Image:
        """
        画像をbase64デコードする
        """
        try:
            decoded_data = base64.b64decode(base64_str)
        except binascii.Error as e:
            if safe:
                print(f"ImageUtil.from_base64: {e}")
                return None
            raise ValueError("Invalid base64 string") from e

        self.image = self.from_buffer(BytesIO(decoded_data))
        return self.image


    def from_file(self, file_path: str) -> Image.Image:
        """
        画像をファイルから読み込む
        """
        if os.path.exists(file_path):
            self.image = Image.open(file_path)
            return self.image
        else:
            raise FileNotFoundError("ImageUtil.from_file: file not found")


    def from_buffer(self, byte: bytes | BytesIO) -> Image.Image:
        if isinstance(byte, bytes):
            buffer = BytesIO(byte)
        else:
            buffer = byte

        buffer.seek(0)
        self.image = Image.open(buffer)
        return self.image


    def to_buffer(self, image: Image.Image = None, f: str = "PNG") -> BytesIO:
        image = image if image is not None else self.absolute_get()
        buffer = BytesIO()

        if f == "JPEG" or f == "JPG":
            image = image.convert("RGB")
        image.save(buffer, format=f)
        buffer.seek(0)

        return buffer


    def to_file(self, image: Image.Image = None, fn: str = None, f: str = "PNG") -> str:
        image = image if image is not None else self.absolute_get()
        fn = fn if fn is not None else "img."+f
        buffer = self.to_buffer(image, f)
        return discord.File(buffer, filename=fn)