import gradio as gr
import time

from modules.api.call_internal import send_request

class ModelList:
    def _check_item(self, item):
        if item in self.items:
            return True
        else:
            raise ValueError("[ModelList]: Invalid item: {item}")

    def __init__(self):
        self.items = [
            "sampler",
            "scheduler",
            "upscaler",
            "checkpoint",
            "vae",
            "LoRA",
            "hypernetwork",
            "textual",
            "scripts",
            "adetailer",
            "controlnet"
        ]
        self.sampler: list[str] = []
        self.scheduler: list[str] = []
        self.upscaler: list[str] = []
        self.checkpoint: list[str] = []
        self.vae: list[str] = []

        self.LoRA: list[str] = []
        self.hypernetwork: list[str] = []
        self.textual: list[str] = []

        self.scripts: list[str] = []

        self.adetailer: list[str] = []
        self.controlnet: list[str] = []

        self.address: dict[str: str] = {
            "sampler": "/sdapi/v1/samplers", # Sampler
            "scheduler": "/sdapi/v1/schedulers", # Scheduler
            "upscaler": "/sdapi/v1/upscalers", # Upscaler
            "checkpoint": "/sdapi/v1/sd-models", # Checkpoint
            "vae": "/sdapi/v1/sd-vae", # VAE
            "LoRA": "/sdapi/v1/loras", # LoRA
            "hypernetwork": "/sdapi/v1/hypernetworks", # Hypernetwork
            "textual": "/sdapi/v1/embeddings", # Textual
            "scripts": "/sdapi/v1/scripts", # Scripts
            "adetailer": "/adetailer/v1/ad_model", # Adetailer
            "controlnet": "/controlnet/model_list" # ControlNet
        }

        self.update_last_run: int = 0

        # init
        self.update()

    def update(self):
        for attr, address in self.address.items():
            try:
                response = send_request(address, {}, "GET")
            except gr.Error:
                gr.Warning("Failed to fetch model list. Please check if the server is running.")
                continue

            if response is None:
                gr.Warning(f"Failed to fetch model list. Please check custom-IP.")
                continue

            setattr(self, attr, response)
            print("[ModelList]: Updated: ", attr)
        self.update_last_run = time.time()

    def __getattr__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        else:
            return None


    def resize(self, item):
        """モデルリストをGradio UIやユーザーフレンドリーな形式に変換"""
        self._check_item(item)
        if item in [
            "sampler", "scheduler", "upscaler", "hypernetwork", "LoRA"
        ]:
            return [
                i["name"]
                for i in getattr(self, item)
                if isinstance(i, dict) and "name" in i.keys()
            ]

        elif item in [
            "checkpoint"
        ]:
            return [
                i["title"]
                for i in getattr(self, item)
                if isinstance(i, dict) and "title" in i.keys()
            ]

        ## TODO: 残り