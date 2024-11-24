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
            every: bool = False

        def get_html():
            if i.every:
                try:
                    html = i.instance.generate_html()
                except Exception as e:
                    print(f"[WARN]: Failed generating HTML ({e})")
                    return f"Exception on converting to HTML ({e})"
                if isinstance(html, str):
                    return html
                else:
                    return "Unknown Error"
            return "Not initialized"

        def load_run():
            i.every = True
            return gr.update(visible=False), gr.update(visible=True)

        def stop_run():
            i.every = False
            return gr.update(visible=True), gr.update(visible=False)

        def search(text):
            if i.every:
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
        stop = gr.Button("Stop", visible=False)

        load.click(
            load_run, outputs=[load, stop]
        )
        stop.click(
            stop_run, outputs=[load, stop]
        )

        with gr.Group(
            elem_id="lora_models_viewer_html_element"
        ):
            html = gr.HTML(value=get_html, every=10)

        search_text.input(
            search, search_text, html
        )