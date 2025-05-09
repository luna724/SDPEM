import base64
from io import BytesIO

from PIL import Image


class ImageGeneration:
    _default_payload = {
                "negative_prompt": "score_6, score_5, score_4, ugly face, low res, interlocked fingers, anatomically incorrect hands, bad anatomy, pony, furry, censored, realistic, pencil art, boy, EasyNegative, badhandv5, By bad artist -neg,  (((public hair), abs)), (bad anatomy:1.4), (low quality, worst quality:1.1), lips, fat, (inaccurate limb:1.2), (Low resolution:1.1), censored, monochrome,",
                "seed": -1,
                "scheduler": "Automatic",
                "batch_size": 2,
                "n_iter": 1,
                "cfg_scale": 7.5,
                "width": 1024,
                "height": 1024,
                "restore_faces": False,
                "tiling": False,
                "denoising_strength": 0.3,
                "enable_hr": False,
                "override_settings": {
                    "CLIP_stop_at_last_layers": 2,
                },
                "alwayson_scripts": {
                    "ADetailer": {
                        "args": [
                            True,
                            False,
                            {
                                "ad_model": "face_yolov8n.pt",
                                "ad_prompt": "",
                                "ad_negative_prompt": "",
                                "ad_denoising_strength": 0.3
                            }
                        ]
                    }
                }
            }

    @staticmethod
    def adjust_prompt(prompt: str | list[str] = None) -> str | None:
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            return ", ".join(prompt)
        else:
            return None


    def __init__(self, is_img2img: bool = False):
        self.is_img2img = is_img2img

        self.prompt: str | None = None
        self.negative_prompt: str | None = None

        self.adetailer_prompt: str | None = None
        self.adetailer_negative_prompt: str | None = None

        self.default_payload: dict = ImageGeneration._default_payload

        self.image: str | None = None

        self.response: dict | None = None


    def set_prompt(
            self, prompt: str | list[str] = None, adetailer_prompt: str | list[str] = None,
            negative_prompt: str | list[str] = None, adetailer_negative_prompt: str | list[str] = None,
    ):
        """
        プロンプトを設定 / Noneの場合更新しない
        :param prompt:
        :param adetailer_prompt:
        :param negative_prompt:
        :param adetailer_negative_prompt:
        :return:
        """

        if prompt is not None:
            self.prompt = self.adjust_prompt(prompt)
        if adetailer_prompt is not None:
            self.adetailer_prompt = self.adjust_prompt(adetailer_prompt)
        if negative_prompt is not None:
            self.negative_prompt = self.adjust_prompt(negative_prompt)
        if adetailer_negative_prompt is not None:
            self.adetailer_negative_prompt = self.adjust_prompt(adetailer_negative_prompt)


    def override_payload(self, **payload):
        """
        self.default_payload を上書きする
        :param payload:
        :return:
        """
        self.default_payload = self.default_payload | payload
    def update_payload(self, **payload): self.override_payload(**payload)


    def set_image(self, image: str | bytes | Image.Image | BytesIO) -> str:
        """
        img2img用の画像を設定する

        :param image:
        :return: base64でエンコードされた画像
        """
        if isinstance(image, str):
            # str の場合 base64済みとみなす
            self.image = image

        elif isinstance(image, bytes):
            # bytes の場合、エンコードだけする
            self.image = base64.b64encode(image).decode("utf-8")

        elif isinstance(image, Image.Image):
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            self.image = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

        elif isinstance(image, BytesIO):
            self.image = base64.b64encode(
                image.getvalue()
            ).decode("utf-8")

        else:
            raise ValueError("Invalid image type. Must be str, bytes, PIL.Image or BytesIO.")

        return self.image


    def unpack_images(
            self, manual_response: dict = None
    ) -> list[Image.Image]:
        """
        返されたb64エンコード画像を PIL画像に変換して返す
        :param manual_response:
        :return:
        """
        response = manual_response if manual_response else self.response
        