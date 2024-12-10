import gradio as gr
import os

import shared
from modules.simple_template import SimpleTemplate
from modules.static_generator import StaticGenerator
from modules.ui_util import browse_file
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Static"

    def index(self):
        return 1

    def ui(self, outlet):
        module = StaticGenerator()
        with gr.Blocks():
            gr.Markdown("Static Prompt set (which one needed)")
            display_name = gr.Textbox(label="Display Name")

            with gr.Row():
                text_params = gr.Textbox(label="Parameters", lines=6, max_lines=999)
                param_image = gr.Image(label="Generated Image", sources=["upload", "clipboard"], type="pil")
            with gr.Row():
                from_json = gr.Textbox(label="From json", lines=1, scale=9)
                json_browse = gr.Button(shared.refresh_button, scale=1)
                json_browse.click(
                    browse_file, outputs=from_json
                )

            with gr.Row():
                overwrite = gr.Checkbox(label="Overwrite")
                no_negative = gr.Checkbox(label="Use default Negative")
                output_json = gr.Checkbox(label="output as json (to /outputs)")
                no_image = gr.Checkbox(label="Don't save Image (A1111/Loadable images still usable)")

            with gr.Accordion("output json setting"):
                author = gr.Textbox(label="value of \"original_author\"")

            save_with_params = gr.Button("Save with Parameters")
            save_with_params.click(
                module.save_template,
                [text_params, param_image, from_json, display_name, overwrite, no_negative, output_json, no_image, author],
                save_with_params
            )