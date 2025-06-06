from modules.api.txt2img import txt2img_api
from webui import UiTabs

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Generation Progress"

    def index(self):
        return 1

    def ui(self, outlet):
        txt2img_api_instance = txt2img_api()
        with gr.Blocks():
            with gr.Row():
                check = gr.Button("Check", variant="primary")
                interrupt = gr.Button("Interrupt", variant="secondary")
                interrupt.click(
                    txt2img_api_instance.interrupt,
                )

            with gr.Row():
                progress = gr.Number(label="Progress", precision=2)
                eta = gr.Textbox(label="ETA", lines=1)
                state = gr.Textbox(label="State", lines=1)

            image = gr.Image(type="pil", sources=["upload"], label="Image", elem_classes="img1024")
            textinfo = gr.Textbox(label="TextInfo")

            check.click(
                txt2img_api_instance.get_progress,
                outputs=[progress, eta, state, image, textinfo]
            )