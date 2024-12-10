import time
from typing import *
import gradio as gr
import os

import shared
from modules.yield_util import yielding_util, new_yield
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
                send_text = new_yield("[TEST]: ")
                yield send_text("Yield testing..")
                time.sleep(7)
                yield send_text("elapsed: 7seconds")
                time.sleep(1)
                yield " ".join(i)
            btn.click(
                get_val, shared.ui_obj["Generation"]["from LoRA"]["meta_mode"], outputs=text
            )