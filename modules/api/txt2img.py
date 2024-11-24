import json
import urllib.request
import urllib.error
import gradio as gr

from modules.util import Util


class txt2img_api(Util):
    def __init__(self, ui_port:int, **payload):
        self.default_payload = payload
        self.ui_port = ui_port

    def generate(self, **override_payload):
        # Code reference: https://gist.github.com/w-e-w/0f37c04c18e14e4ee1482df5c4eb9f53
        payload = self.default_payload | override_payload
        data = json.dumps(payload).encode("utf-8")
        try:
            request = urllib.request.Request(
                f'http://127.0.0.1:{self.ui_port}/sdapi/v1/txt2img',
                headers={'Content-Type': 'application/json'},
                data=data,
            )
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as e:
            print(f"[FATAL]: HTTPError in txt2img/generate ({e})")
            raise gr.Error("HTTPError occurred. you need launch A1111/sd-webui with --api argument, and port are correctly?")
        return json.loads(response.read().decode('utf-8'))
