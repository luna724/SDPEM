import gradio as gr
import os
import shared

from modules.forever.from_images import ForeverGenerationFromImages 
from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent
from modules.utils.lora_util import list_lora_with_tags
# from modules.api.v1.items import sdapi
from modules.sd_param import get_sampler, get_scheduler
from webui import UiTabs
from typing import Callable
from utils import *
from pathlib import Path


class ImageToPrompt(UiTabs):
    def title(self) -> str:
        return "from Images"

    def index(self) -> int:
        return 3

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        forever_generation_from_images = RegisterComponent(
            Path("./defaults/forever_generation.from_images.json"),
            "forever_generation/from_images",
        )
        r = forever_generation_from_images.register
        default = forever_generation_from_images.get()

        with gr.Blocks():
            with gr.Blocks():
                with gr.Row():
                    with gr.Column(scale=2):
                        use_images = r(
                            "use_images",
                            gr.Files(
                                value=None, type="filepath",
                                label="Images to use (.png, .jpg(jpeg))",
                                interactive=True,
                            )
                        )
                        
                    with gr.Column(scale=3):
                        use_folder = r(
                            "use_folder",
                            gr.Dropdown(
                                value=default.use_folder, 
                                choices=default.use_folder or [],
                                label="Folder to use",
                                interactive=True,
                                multiselect=True,
                            )
                        )
                        browse_folder_btn = gr.Button("Browse", size="lg")
                        
                        async def on_browse_folder_btn_click(use_folder):
                            if use_folder is None: use_folder = []
                            f = select_folder()
                            if f and os.path.exists(f):
                                use_folder.append(f)
                                return gr.Dropdown(
                                    value=use_folder, choices=use_folder
                                )
                            return use_folder
                        browse_folder_btn.click(
                            fn=on_browse_folder_btn_click,
                            inputs=[use_folder],
                            outputs=[use_folder],
                            show_progress=False,
                        )
                
                with gr.Row():
                    tag_count_weight = r(
                        "tag_count_weight",
                        gr.Slider(
                            0.1,
                            10,
                            step=0.1,
                            value=default.tag_count_weight,
                            label="Tag Count Weight Multiplier",
                            info="higher value to increase  (weight = 0.1 * (tag_count*this))",
                            scale=4,
                        ),
                    )
                    use_booru_to_no_param_images = r(
                        "use_booru_to_no_param_images",
                        gr.Checkbox(
                            value=default.use_booru_to_no_param_images,
                            label="[wip] Use booru to get tags for images without parameters",
                            info="If enabled, images without parameters will use booru to get tags",
                            scale=4,
                        ),
                    )
            
            # save_all_param = gr.Button("Save current parameters", variant="secondary")
            # c=gr.Textbox(visible=False, value="default")
            # save_all_param.click(
            #     fn=forever_generation_from_images.save_ui,
            #     inputs=[c] + forever_generation_from_images.values(),
            #     outputs=[],
            # )
            
            # generate.click(
            #     fn=instance.start,
            #     inputs=var,
            #     outputs=[eta, progress_bar_html, image, output, skipped_img, stopping_gen],
            # )
            # stop.click(fn=instance.stop_generation, inputs=[], outputs=[])