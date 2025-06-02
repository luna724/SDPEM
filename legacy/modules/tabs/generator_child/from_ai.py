import inspect
import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from modules.lora_generator import LoRAGeneratingUtil
from modules.lora_viewer import LoRADatabaseViewer
from modules.ui_util import (
    ItemRegister,
    bool2visible,
    checkbox_default,
    browse_directory,
)
from modules.util import Util
from webui import UiTabs


class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "generator_child")

    def title(self):
        return "AI-Generation"

    def index(self):
        return 4

    def ui(self, outlet):
        def setter(d, k, i):
            return ItemRegister.dynamic_setter(d, k, i, "Generation", self.title())

        register = ItemRegister(setter=setter)
        default_fp = os.path.join(
            os.getcwd(), "configs/default/generator-ai_generation.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(
                    os.getcwd(), "configs/default/default/generator-ai_generation.json"
                ),
                default_fp,
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        available_modes = [
            "GPT-2", "Word2Vec", "LLaMA(7B, 13B)"
        ]
        with gr.Blocks():
            selected_model = gr.Dropdown(
                choices=available_modes, value="GPT-2", interactive=False
            )

