from typing import *
import gradio as gr
import os

import shared
from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "settings_child")

    def title(self):
        return "Settings"

    def index(self):
        return -1

    def ui(self, outlet):
        with gr.Blocks():
            text = gr.Textbox()
            btn = gr.Button("test")

            def get_val(i: Iterable):
                return " ".join(i)
            btn.click(
                get_val, shared.ui_obj["Generation"]["from LoRA"]["meta_mode"], outputs=text
            )