import gradio as gr
import os

from webui import UiTabs


class Lora(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "models_child")


    def title(self):
        return "LoRA"

    def index(self):
        return -1

    def ui(self, outlet):
        text = gr.Textbox(label="hELLO!")