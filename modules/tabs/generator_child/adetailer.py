import gradio as gr
import os

import shared
from modules.adetailer import ADetailer
from modules.simple_template import SimpleTemplate
from modules.ui_util import browse_directory
from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "generator_child")

    def title(self):
        return "ADetailer"

    def index(self):
        return 9

    def ui(self, outlet):
        module = ADetailer()
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
                base_image = gr.Image(label="Base Image", sources="upload", type="pil")

            step = gr.Slider(1, 150, step=1, value=21, label="AD Steps")

            def pn():
                return (
                    gr.Textbox(
                        label="ADetailer Prompt", placeholder="blank to get from image param"
                    ),
                    gr.Textbox(
                        label="ADetailer Negative Prompt", placeholder="blank to get from image param"
                    )
                )

            elements = []
            with gr.Tabs():
                for i in range(1, 7): # 1..6
                    with gr.Tab(f"ADetailer Model {i}"):
                        m = gr.Dropdown(
                            label=f"{i} AD Model",
                            choices=module.list_models(),
                            value="None"
                        )
                        with gr.Row():
                            p, n = pn()
                            elements += [m, p, n]

            out_image = gr.Image(
                label="Output", type="pil", interactive=False, show_download_button=True
            )

            save_with_params = gr.Button("Infer", variant="primary")
            save_with_params.click(
                module.webui_tunnel,
                inputs=[
                    mode, base_image, batch_folder, step
                ] + elements,
                outputs=out_image
            )

            def mode_change(mode): # Single なら一つ目が表示
                return mode=="Single", mode!="Single"

            mode.change(
                mode_change,
                inputs=mode,
                outputs=[single, batch]
            )