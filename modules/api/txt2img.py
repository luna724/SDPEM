import json
import time
import urllib.request
import urllib.error
import gradio as gr

from modules.util import Util
from concurrent.futures import ThreadPoolExecutor

from modules.api.server_ip import server_ip

class txt2img_api(Util):
    @staticmethod
    def _send_request(url, data):
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
                data=data,
            )

            with urllib.request.urlopen(req) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            print(f"HTTP error: {e.code} - {e.reason}")
            raise gr.Error(f"HTTP error: {e.code} - {e.reason}.\nDid you launch SD-WebUI with --api argument?")
        except urllib.error.URLError as e:
            print(f"URL error: {e.reason}.\nre-check custom IP and try again.")
            return None

    def __init__(self, ui_port:int, **payload):
        self.default_payload = payload
        self.ui_port = ui_port
        self.executor = ThreadPoolExecutor(max_workers=1)

    def generate(self, **override_payload):
        """
        generateリクエストをスレッドで実行し、
        リクエストの応答待ち中に他のバックグラウンド処理を続ける。
        """
        payload = self.default_payload | override_payload
        data = json.dumps(payload).encode("utf-8")

        # スレッドでリクエストを実行
        future = self.executor.submit(self._txt2img_api, data)

        # リクエスト中に他の処理を実行
        while not future.done():
            self.do_other_processing()
            time.sleep(2.5)  # CPU負荷を避けるためウェイトを挟む

        # 結果を取得する
        response = future.result()
        return json.loads(response)

    def _txt2img_api(self, data):
        """
        実際にリクエストを送信する同期的な処理（非公開）。
        """
        url = f"/sdapi/v1/txt2img"
        return self._send_request(url, data)

    def do_other_processing(self):
        """
        リクエスト中に実行する処理を記述する。
        """
        pass
