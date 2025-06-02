import base64
from io import BytesIO

from PIL import Image

from modules.api.upscalerapi import UpscalerAPI


class Upscaler:
    def __init__(self):
        self.api = UpscalerAPI()

    @staticmethod
    def list_models() -> list[str]:
        return [
            "Lanczos", "Nearest", "DAT x2", "DAT x3", "DAT x4", "DAT_x4", "ESRGAN_4x", "LDSR", "R-ESRGAN 4x+",
            "R-ESRGAN 4x+ Anime6B", "ScuNET", "ScuNET PSNR", "SwinIR 4x"
        ]

    def single(
        self,
        base_image: Image.Image,
        resize_to: int,
        model: str
    ) -> Image.Image:
        """
        単体の画像をアップスケールする
        """
        model_payload = {
            "upscaler_1": model,
            "upscaling_resize": resize_to
        }

        generator = self.api.call(base_image, **model_payload)
        last_value = None
        try:
            while True:
                last_value = next(generator)
        except StopIteration as e:
            data = e.value

        response = data[0]
        image = base64.b64decode(response.get("image", ""))
        image = Image.open(BytesIO(image))
        return image