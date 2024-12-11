import json
import time
import urllib.request
import urllib.error
import gradio as gr

from modules.util import Util
from concurrent.futures import ThreadPoolExecutor

class txt2img_api(Util):
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
        future = self.executor.submit(self._send_request, data)

        # リクエスト中に他の処理を実行
        while not future.done():
            self.do_other_processing()
            time.sleep(2.5)  # CPU負荷を避けるためウェイトを挟む

        # 結果を取得する
        response = future.result()
        return json.loads(response)

    def _send_request(self, data):
        """
        実際にリクエストを送信する同期的な処理（非公開）。
        """
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.ui_port}/sdapi/v1/txt2img",
            headers={"Content-Type": "application/json"},
            data=data,
        )
        with urllib.request.urlopen(request) as response:
            return response.read().decode("utf-8")

    def do_other_processing(self):
        """
        リクエスト中に実行する処理を記述する。
        """
        pass