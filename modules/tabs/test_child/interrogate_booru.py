from modules.models import deepbooru
from webui import UiTabs

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Interrogate Booru"

    def index(self):
        return 1

    def ui(self, outlet):
        with gr.Blocks():
            with gr.Row():
                image = gr.Image(type="pil", sources=["upload"], label="Image")
                output = gr.Textbox(label="Output", lines=4)
            with gr.Row():
                threshold = gr.Slider(0, 1, step=0.05, value=0.75, label="Threshold", scale=3)

            def interrogate(image, threshold) -> str:
                res = deepbooru.default.interrogate(image, threshold)
                return ", ".join(res.keys())

            infer = gr.Button("Interrogate")
            infer.click(
                interrogate,
                inputs=[image, threshold],
                outputs=output
            )
