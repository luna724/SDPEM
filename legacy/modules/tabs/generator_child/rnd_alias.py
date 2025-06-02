import inspect
import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from modules.api.txt2img import txt2img_api
from modules.from_lora_forever_generation import FromLoRAForeverGeneration
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
        return "from Alias"

    def index(self):
        return 0

    def ui(self, outlet):
        def setter(d, k, i):
            return ItemRegister.dynamic_setter(d, k, i, "Generation", self.title())

        viewer = LoRADatabaseViewer()
        generator = LoRAGeneratingUtil()
        forever_generator = FromLoRAForeverGeneration()
        register = ItemRegister(setter=setter)
        default_fp = os.path.join(
            os.getcwd(), "configs/default/generator-from_alias.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(os.getcwd(), "configs/default/default/generator-from_alias.json"), default_fp
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        gr.Markdown(
            "Generate from your Prompt alias"
        )

        with gr.Blocks():
            @register.register("bcf_blacklist")
            def func_bcf_blacklist():
                return gr.Textbox(
                    label="tag blacklist (BooruCaptionFilter)",
                    lines=4,
                    placeholder="separate with comma (,)\nYou can use $regex={regex_pattern} $includes={text}\neg. $regex=^white == blacklisted starts white\neg. $includes=thighhighs == blacklisted includes thighhighs (instead. $regex=thighhighs). etc..",
                    value=default.bcf_blacklist, visible=True
                )
            bcf_blacklist = func_bcf_blacklist()

            @register.register("booru_threshold")
            def func_threshold():
                return gr.Slider(
                    0,
                    1,
                    step=0.05,
                    value=default.booru_threshold,
                    label="BooruCaptionFilter Booru Threshold",
                )
            booru_threshold = func_threshold()

            @register.register("bcf_dont_discard", "bcf_invert", "bcf_filtered_path")
            def func_bcf_opts():
                return (
                    gr.Checkbox(
                        label="[BCF] Don't Discard blacklisted image",
                        value=default.bcf_dont_discard,
                        scale=4,
                    ),
                    gr.Checkbox(
                        label="[BCF] Invert target image (whitelisted)",
                        value=default.bcf_invert,
                        scale=5,
                    ),
                    gr.Textbox(
                        label="[BCF] blacklisted image output path",
                        value=default.bcf_filtered_path,
                        scale=6,
                    )
                )

            @register.register("bcf_enable")
            def func_bcf_enable():
                return gr.Checkbox(
                    label="[BCF] Enable",
                    value=default.bcf_enable,
                    scale=10
                )

            bcf_enable = func_bcf_enable()
            with gr.Row():
                bcf_dont_discard, bcf_invert, bcf_filtered_path = func_bcf_opts()
                bcf_browse_dir = gr.Button(value=shared.refresh_button, size="lg", scale=2)
                bcf_browse_dir.click(browse_directory, outputs=bcf_filtered_path)

            @register.register("header", "lower")
            def func_head_and_low():
                return (
                    gr.Textbox(
                        label="Header prompt",
                        placeholder="this prompts always add and not affect max tags limit",
                        max_lines=3,
                        elem_id="generate-from_lora-header_prompt",
                        value=default.header,
                    ),
                    gr.Textbox(
                        label="Lower prompt",
                        placeholder="this prompts always add and not affect max tags limit",
                        max_lines=3,
                        elem_id="generate-from_lora-lower_prompt",
                        value=default.lower,
                    ),
                )
            header, lower = func_head_and_low()

            with gr.Row():
                output = gr.Textbox(label="Output prompt", show_copy_button=True, lines=5)

                @register.register("max_tags")
                def func_use_tags_related():
                    return (
                        gr.Slider(
                            label="Max tags",
                            minimum=1,
                            maximum=999,
                            step=1,
                            value=default.max_tags,
                            elem_id="generate-from_lora-max_tags",
                        )
                    )
                with gr.Column():
                    max_tags = func_use_tags_related()
                    infer = gr.Button("Infer", variant="primary")

            infer.click(

            )