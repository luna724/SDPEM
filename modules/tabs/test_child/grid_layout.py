import shared
from modules import deepbooru
from modules.tag_compare import TagCompareUtilities
from modules.ui_util import browse_directory
from webui import UiTabs
import modules.bert
import modules.tag_compare

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Grid Layout"

    def index(self):
        return 4

    def ui(self, outlet):
        with gr.Blocks():
            with gr.Row():
                image_dir = gr.Textbox(label="Image Dir", lines=1, scale=8)
                browse = gr.Button(shared.refresh_button)
                browse.click(
                    browse_directory,
                    outputs=image_dir,
                )

            with gr.Row():
                text = gr.Radio(
                    choices=["filename", "caption (txt)"],
                    value="filename", label="TextMode"
                )

