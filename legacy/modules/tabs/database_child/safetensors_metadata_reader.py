from typing import Literal

import gradio as gr
import os

import shared
from modules import ui_util
from modules.lora_metadata_util import LoRAMetadataReader
from webui import UiTabs


class Lora(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "database_child")


    def title(self):
        return "LoRA (Metadata)"

    def index(self):
        return 1

    def ui(self, outlet):
        with gr.Row():
            based_model = gr.Textbox(label="Base Model", placeholder="Unknown")
            version = gr.Textbox(
                label="Detected base Model version", lines=1
            )

        with gr.Row():
            fp = gr.Textbox(label="Target LoRA (only safetensors)", placeholder="/", scale=8)
            browse = gr.Button(shared.refresh_button, scale=2)
            browse.click(
                ui_util.browse_file, outputs=fp
            )
        show = gr.Button("Show", variant="primary")

        with gr.Accordion("Raw", open=False):
            metadata = gr.Textbox(
                    label="Metadata", lines=10, max_lines=120, show_copy_button=True,
                    placeholder="{}", interactive=False
            )

        def temp(fp):
            reader = LoRAMetadataReader(fp)
            if reader.loadable:
                return reader.metadata, reader.detect_base_model_for_ui()
            else:
                raise gr.Error("metadata cannot loadable")

        show.click(
            fn=temp, inputs=fp, outputs=[metadata, version]
        )