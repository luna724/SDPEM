import base64
import json
import time
from io import BytesIO
from typing import Any, Generator

from PIL import Image

from modules.api.txt2img import txt2img_api
from modules.image_progress import ImageProgressAPI


class ADetailerAPI(txt2img_api):
    def __init__(self, refresh_rate = 1.5, *args, **payload):
        super().__init__(refresh_rate, *args, **payload)

        force_payload = {
            "init_images": [],
            "alwayson_scripts": {
                "ADetailer": {
                    "args": [
                        True,
                        True,
                        {
                            "ad_model": "face_yolov8n.pt",
                            "ad_prompt": "",
                            "ad_negative_prompt": ""
                        }
                    ]
                }
            }
        }
        self.default_payload = self.default_payload | force_payload

    def _img2img_api(self, data):
        url = f"/sdapi/v1/img2img"
        return self._send_request(url, data)

    def call(self, image: Image.Image, **override_payload) -> tuple[bool|dict, tuple[str, str, str, bool]]:
        """
        生成中には Falsy, [status, eta, progress, interrupted] を返し
        生成完了時には Response.json, [status, eta, progress, interrupted] を返す
        """
        payload = self.default_payload | override_payload
        print(f"[ADetailerAPI]: Generation started! payload: {payload}")

        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)
        payload["init_images"] = [
            base64.b64encode(buffer.getbuffer()).decode("utf-8"),
        ]

        future = self.executor.submit(self._img2img_api, payload)
        last = None
        while not future.done():
            prog, eta, state, image, _ = self.get_progress()
            if state is None:
                time.sleep(self.refresh_rate)
                continue

            current_step = state["sampling_step"]
            steps = state["sampling_steps"]
            if steps == 0:
                time.sleep(self.refresh_rate)
                continue

            last = (
                ImageProgressAPI.status_text(current_step, steps),
                ImageProgressAPI.resize_eta(eta), image,
                ImageProgressAPI.progress_bar_html(int((current_step / steps) * 100), eta),
                state["interrupted"]
            )
            # print("yielding..")
            yield (False, last)
            time.sleep(self.refresh_rate)  # WinError 10048を防ぐ

        response = future.result()
        return (json.loads(response), last)