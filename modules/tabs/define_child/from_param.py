import gradio as gr
import os

from modules.simple_template import SimpleTemplate
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Simple-Template"

    def index(self):
        return 0

    def ui(self, outlet):
        module = SimpleTemplate()
        with gr.Blocks():
            gr.Markdown("from Parameters (which one needed)")
            display_name = gr.Textbox(label="DisplayName")

            with gr.Row():
                text_params = gr.Textbox(label="Parameters", lines=6, max_lines=999)
                param_image = gr.Image(label="Generated Image", sources=["upload", "clipboard"], type="pil")

            with gr.Row():
                overwrite = gr.Checkbox(label="Overwrite")
                auto_convert = gr.Checkbox(label="Auto-Convert Character's data", value=True)
                no_negative = gr.Checkbox(label="Don't save Negative")
                with gr.Column():
                    include_extensions = gr.Checkbox(label="[β]: Include extension", interactive=False)
                    #gr.Markdown(f"[v5.0.0: convert-supported extensions]({os.path.join(os.getcwd(), 'docs/convert-supported-extensions.md')})")

            save_with_params = gr.Button("Save with Parameters")
            save_with_params.click(
                module.tunnel_for_ui_from_param,
                [text_params, param_image, display_name, overwrite, auto_convert, no_negative, include_extensions],
                save_with_params
            )