import shutil

import gradio as gr
import os

import shared
from jsonutil import JsonUtilities
from modules.ui_util import ItemRegister, browse_file, browse_directory
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "caption_utils")

    def title(self):
        return "Caption Util"

    def index(self):
        return 100000

    def ui(self, outlet):
        def setter(d, k, i):
            return ItemRegister.dynamic_setter(d, k, i, "Caption-Util")

        register = ItemRegister(setter=setter).register
        default_fp = os.path.join(
            os.getcwd(), "configs/default/caption_util.json"
        )
        if not os.path.exists(default_fp):
            shutil.copy(
                os.path.join(
                    os.getcwd(), "configs/default/default/caption_util.json"
                ),
                default_fp,
            )
        default_file = JsonUtilities(default_fp)
        default = default_file.make_dynamic_data()

        with gr.Blocks():
            with gr.Group():
                gr.Markdown("preprocessor")

                with gr.Row():
                    @register("target_dir", "caption_ext")
                    def fun_target_dir():
                        return (
                            gr.Textbox(
                                label="Target dir",
                                interactive=True, placeholder="including images folder",
                                value=default.target_dir,
                                scale=10
                            ),
                            gr.Textbox(
                                label="Caption ext",
                                value=default.caption_ext, placeholder=".txt",
                                scale=10
                            )
                        )
                    target_dir, caption_ext = fun_target_dir()
                    browse = gr.Button(shared.refresh_button)
                    browse.click(
                        fn=browse_directory,
                        outputs=[target_dir]
                    )

                with gr.Row():
                    @register("autoscale_caption", "convert_to_space", "convert_to_lowercase", "png_exist_check")
                    def fun_processor_2():
                        return (
                            gr.Checkbox(
                                label="Autoscale caption",
                                value=default.autoscale_caption
                            ),
                            gr.Checkbox(
                                label="Convert to space",
                                value=default.convert_to_space
                            ),
                            gr.Checkbox(
                                label="Convert to Lowercase",
                                value=default.convert_to_lowercase
                            ),
                            gr.Checkbox(
                                label="PNG exist check",
                                value=default.png_exist_check
                            )
                        )
                    autoscale_caption, convert_to_space, convert_to_lowercase, png_exist_check = fun_processor_2()

            super().ui(outlet)