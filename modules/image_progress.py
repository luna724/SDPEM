import asyncio
from typing import Any

from PIL.ImageFile import ImageFile

import shared
from modules.api.call_internal import get_request_with_status

import PIL.Image
from io import BytesIO
import base64
import json
from typing import *

class _ImageProgressAPI:
    @staticmethod
    def resize_eta(eta: float) -> str:
        """ETA を h/m/s の形式に変換する"""
        if eta == -1:
            return "N/A"

        converted = int(eta)
        h = converted // 3600
        converted -= h * 3600
        m = converted // 60
        converted -= m * 60
        s = converted

        eta = f""
        if h > 0:
            eta += f"{h}h "
        if m > 0:
            eta += f"{m}m "
        if s > 0:
            eta += f"{s}s"

        return eta.strip()

    @staticmethod
    def status_text(s: int, total_s: int) -> str:
        """受け取った引数を (s/total_s (steps)) (s/total_s%) に変換する"""
        percentage = "{:.1f}".format(s / total_s * 100)
        return f"({s}/{total_s} (steps)) ({percentage}%)"

    @staticmethod
    def progress_bar_html(progress: int, eta: float) -> str:
        """UIのプログレスバーのHTML"""
        eta = ImageProgressAPI.resize_eta(eta)
        return f"""
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 8px; overflow: hidden;">
            <div style="width: {progress}%; height: 30px; background-color: #76c7c0; transition: width 0.3s;"></div>
        </div>
        <p style="text-align: center;">ETA: {eta} ({progress}%)</p>
        """

    async def _update(self):
        while True:
            # ごみ処理
            if self.sleep_interval >= 120:
                self.sleep_interval = 1

            self.sleep_interval -= 1
            await asyncio.sleep(1)
            if self.sleep_interval <= 0:
                await self.update_image()


    def __init__(self):
        self.url = "/sdapi/v1/progress"
        self.sleep_interval: int = 1

        self.last_image: PIL.Image = None
        # 違いは生成完了したものかどうか
        self.last_generated_image: PIL.Image = None

        shared.loop.create_task(self._update())

    def get_progress(self) -> tuple[str, str, str, PIL.Image, str]:
        response = get_request_with_status(self.url, {})

        try:
            # 404 は 30秒の更新クールダウンを付けて last_image を返す
            # 500, 501 は 5秒の更新クールダウンを付けて last_image を返す
            if response.status_code == 404:
                self.sleep_interval += 30
                return "N/A", "N/A", "{}", self.last_image, ""
            elif response.status_code in [500, 501]:
                self.sleep_interval += 5
                return "N/A", "N/A", "{}", self.last_image, ""
            response.raise_for_status()

            data = json.loads(response.content.decode("utf-8"))
            progress = data.get("progress", "N/A")
            eta = data.get("eta_relative", "N/A")
            state = data.get("state", "{}")
            textinfo = data.get("textinfo", "N/A")
            image = data.get("current_image", None)

            try:
                if image is None:
                    image = self.last_image
                else:
                    image = PIL.Image.open(BytesIO(base64.b64decode(image)))
            except TypeError:
                pass
            except Exception as e:
                print(f"[ImageProgressAPI]: An Error occurred in preview image: {e}")
                raise e # 親try-except にキャッチさせる
            if image is not None:
                self.last_image = image

            return progress, eta, state, self.last_image, textinfo

        except KeyError as e:
            print(f"KeyError in ImageProgressAPI:get_progress: {e}")
            return "N/A", "N/A", "{}", self.last_image, ""

        except Exception as e:
            print(f"Unknown error in ImageProgressAPI:get_progress: {e}")
            return "N/A", "N/A", "{}", self.last_image, ""

    async def update_image(self):
        ## TODO: 生成完了を検知し、last_generated_image の保存を行う
        response = get_request_with_status(self.url, {})

        try:
            response.raise_for_status()
            data = json.loads(response.content.decode("utf-8"))
            image = data.get("current_image", None)
            if image is None:
                return

            image = PIL.Image.open(BytesIO(base64.b64decode(image)))
            if image:
                self.last_image = image
                return

        except Exception as e:
            print(f"Error in ImageProgressAPI:update_image: {e}")
            return

ImageProgressAPI = _ImageProgressAPI()