import base64
import json
import time
import urllib.request
import urllib.error
import gradio as gr
from PIL import Image
from io import BytesIO

from modules.util import Util
from concurrent.futures import ThreadPoolExecutor

from modules.api.server_ip import server_ip

class txt2img_api(Util):
    @staticmethod
    def _send_request(url, data, method="POST"):
        """Sends a request to the specified URL with the given data.

        Args:
            url: The URL to send the request to.
            data: The data to send with the request.

        Returns:
            The response from the server, or None if an error occurred.
        """
        try:
            req = urllib.request.Request(
                f"http://{server_ip.ip}:{server_ip.port}"+url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data).encode("utf-8"),
                method=method,
            )

            with urllib.request.urlopen(req) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            print(f"HTTP error: {e.code} - {e.reason}")
            raise gr.Error(f"HTTP error: {e.code} - {e.reason}.\nDid you launch SD-WebUI with --api argument?")
        except urllib.error.URLError as e:
            print(f"URL error: {e.reason}.\nre-check custom IP and try again.")
            return None

    def __init__(self, *args, **payload):
        self.default_payload = payload
        self.executor = ThreadPoolExecutor(max_workers=2) # メインと progress まで並列実行可

    def generate(self, **override_payload):
        """
        generateリクエストをスレッドで実行し、
        リクエストの応答待ち中に他のバックグラウンド処理を続ける。
        """
        payload = self.default_payload | override_payload
        data = payload

        # スレッドでリクエストを実行
        future = self.executor.submit(self._txt2img_api, data)

        # リクエスト中に他の処理を実行
        while not future.done():
            self.get_progress()
            time.sleep(2.5)  # CPU負荷を避けるためウェイトを挟む

        # 結果を取得する
        response = future.result()
        return json.loads(response)

    def _txt2img_api(self, data):
        """
        実際にリクエストを送信する同期的な処理。
        """
        url = f"/sdapi/v1/txt2img"
        return self._send_request(url, data)

    def interrupt(self):
        self._send_request("/sdapi/v1/interrupt", {})
        gr.Warning("Interrupting...")
        return

    def get_progress(self):
        response = self._send_request(
            "/sdapi/v1/progress", {}, "GET"
        )
        response = json.loads(response)
        progress = response["progress"]
        eta = response["eta_relative"]
        state = response["state"]
        try:
            current_image = Image.open(BytesIO(base64.b64decode(response["current_image"])))
        except Exception as e:
            print(f"[txt2img]: An Error occurred in preview image: {e}")
            current_image = None
        textinfo = response["textinfo"]
        return progress, eta, state, current_image, textinfo
