from typing import Literal

import gradio as gr
import os

from modules.lora_viewer import LoRADatabaseViewer
from webui import UiTabs


class Lora(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "database_child")


    def title(self):
        return "LoRA (Models)"

    def index(self):
        return 1

    def ui(self, outlet):
        class i:
            instance:LoRADatabaseViewer = LoRADatabaseViewer()

        def get_html():
            try:
                html = i.instance.generate_html()
            except Exception as e:
                print(f"[WARN]: Failed generating HTML ({e})")
                return f"Exception on converting to HTML ({e})"
            if isinstance(html, str):
                return html
            else:
                return "Unknown Error"

        def load_run():
            return gr.update(visible=False), gr.update(visible=True), get_html()

        def stop_run():
            return get_html()

        def search(text):
            i.instance.add_filter(
                text, keyword_enable=True
            )
            return get_html()

        with gr.Row():
            search_text = gr.Textbox(
                label="Search", placeholder="$modelID={ID_in_civitAI}; $lora={LoRA Trigger}; or {filename}\neg. luna724 $lora=luna724LoRA;",
                lines=2, max_lines=2, scale=7
            )

        load = gr.Button("Load", variant="primary")
        stop = gr.Button("Refresh", visible=False)

        with gr.Group(
            elem_id="lora_models_viewer_html_element"
        ):
            html = gr.HTML(value="Not Initialized")

        search_text.input(
            search, search_text, html
        )

        load.click(
            load_run, outputs=[load, stop, html]
        )
        stop.click(
            stop_run, outputs=html
        )