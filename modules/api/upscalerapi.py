import base64
import json
import time
from io import BytesIO

from PIL import Image

from modules.api.txt2img import txt2img_api
from modules.image_progress import ImageProgressAPI


class UpscalerAPI(txt2img_api):
    def __init__(self, refresh_rate = 1.5, *args, **payload):
        super().__init__(refresh_rate, *args, **payload)

        self.default_payload = {
            "resize_mode": 0,
            "show_extras_results": True,
            "upscaling_resize": 2,
            "upscaler_1": "None",
            "image": ""
        }

    def _extra_api(self, data):
        url = "/sdapi/v1/extra-single-image"
        return self._send_request(url, data)

    def call(self, image: Image.Image, **override_payload):
        payload = self.default_payload | override_payload

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        payload["image"] = base64.b64encode(buffer.getvalue()).decode("utf-8")

        future = self.executor.submit(self._extra_api, payload)
        last = None
        while not future.done():
            prog, eta, state, image, _ = self.get_progress()
            if state is None:
                #print("state is none, skipping.")
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