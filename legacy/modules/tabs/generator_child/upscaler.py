import gradio as gr
import os

import shared
from modules.adetailer import ADetailer
from modules.simple_template import SimpleTemplate
from modules.ui_util import browse_directory
from modules.upscaler import Upscaler
from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "generator_child")

    def title(self):
        return "Upscaler"

    def index(self):
        return 10

    def ui(self, outlet):
        module = Upscaler()
        with gr.Blocks():
            mode = gr.Dropdown(
                label="Mode",
                choices=["Single", "Batch"],
                value="Single"
            )
            with gr.Row(visible=False) as batch:
                batch_folder = gr.Textbox(label="Batch Folder", placeholder="Batch Folder Path", scale=8)
                browse = gr.Button(shared.browse_directory)
                browse.click(
                    browse_directory,
                    outputs=batch_folder
                )

            with gr.Row(visible=True) as single:
                image = gr.Image(label="Image", type="pil", sources="upload")

            with gr.Row():
                resize_to = gr.Slider(
                    label="Resize to",
                    minimum=1,
                    maximum=8,
                    step=0.01,
                    value=2
                )
                upscaler = gr.Dropdown(
                    label="Upscaler", value="R-ESRGAN 4x+ Anime6B",
                    choices=["Lanczos", "Nearest", "DAT x2", "DAT x3", "DAT x4", "DAT_x4", "ESRGAN_4x", "LDSR", "R-ESRGAN 4x+", "R-ESRGAN 4x+ Anime6B", "ScuNET", "ScuNET PSNR", "SwinIR 4x"],
                )

            out = gr.Image(label="Output Image", interactive=False)
            run = gr.Button("Infer", variant="primary")
            run.click(
                module.single,
                inputs=[image, resize_to, upscaler],
                outputs=out
            )

            def mode_change(mode): # Single なら一つ目が表示
                return mode=="Single", mode!="Single"

            mode.change(
                mode_change,
                inputs=mode,
                outputs=[single, batch]
            )