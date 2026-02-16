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
        return "from Image"

    def index(self) -> int:
        return 3

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        instance = ForeverGenerationFromImages()
        forever_generation_from_images = RegisterComponent(
            Path("./defaults/forever_generation.from_images.json"),
            "forever_generations/from_images",
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
                                value=default.use_folder, label="Folder to use",
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
            
            with gr.Row():
                with gr.Accordion(label="Prompt Settings", open=False):
                    with gr.Row():
                        tags = r(
                            "tags",
                            gr.Number(
                                label="tag count",
                                value=default.tags,
                                precision=0,
                                scale=3,
                            ),
                        )
                        random_rate = r(
                            "random_rate",
                            gr.Slider(
                                1,
                                10,
                                step=0.1,
                                value=default.random_rate,
                                label="Random rate",
                                info="Random rate for the tag to be included in the prompt",
                                scale=4,
                            ),
                        )
                    with gr.Row():
                        add_lora_name = r(
                            "add_lora_name",
                            gr.Checkbox(
                                value=default.add_lora_name,
                                label="Add LoRA name to prompt",
                                info="If disabled, the LoRA name will be filtered from randomly selected tags",
                                scale=2,
                            ),
                        )
                    header = r(
                        "header",
                        gr.Textbox(
                            label="Prompt Header",
                            placeholder="Enter the prompt header",
                            lines=2,
                            max_lines=5,
                            value=default.header,
                        ),
                    )
                    footer = r(
                        "footer",
                        gr.Textbox(
                            label="Prompt Footer",
                            placeholder="Enter the prompt footer",
                            lines=2,
                            max_lines=5,
                            value=default.footer,
                        ),
                    )
                    negative = r(
                        "negative",
                        gr.Textbox(
                            label="Negative Prompt",
                            placeholder="Enter the negative prompt",
                            lines=2,
                            max_lines=5,
                            value=default.negative,
                        ),
                    )
                    with gr.Row():
                        prompt_weight_chance = r(
                            "prompt_weight_chance",
                            gr.Slider(
                            0, 1, label="Add prompt weight change",
                            info="0 to disable", value=default.prompt_weight_chance, step=0.01
                            ),
                        )
                        with gr.Column():
                            prompt_weight_min = r(
                                "prompt_weight_min",
                                gr.Slider(
                                0, 2, step=0.01, value=default.prompt_weight_min, label="Prompt weight min",
                                info="Minimum prompt weight",
                                ),
                            )
                            prompt_weight_max = r(
                                "prompt_weight_max",
                                gr.Slider(
                                    0, 2, step=0.01, value=default.prompt_weight_max, label="Prompt weight max",
                                    info="Maximum prompt weight",
                                )
                            )
                    with gr.Row():
                        remove_character = r(
                            "remove_character",
                            gr.Checkbox(
                                value=default.remove_character, label="Remove additional character tags",
                            ),
                        )
                    instance_blacklist = r(
                        "instance_blacklist",
                        gr.Textbox(
                            label="Instance Blacklist",
                            placeholder="Enter regex patterns (comma or newline separated)",
                            value=default.values.get("instance_blacklist", ""),
                            lines=2,
                            max_lines=5,
                            info="Captured at Start, compiled as regex, and applied only to that run.",
                        ),
                    )

                with gr.Accordion(label="Parameter Settings", open=False):
                    with gr.Row():
                        s_method = r(
                            "s_method",
                            gr.Dropdown(
                                choices=await get_sampler(),
                                label="Sampling Methods",
                                value=default.s_method,
                                multiselect=True,
                                scale=6,
                            ),
                        )
                        scheduler = r(
                            "scheduler",
                            gr.Dropdown(
                                choices=await get_scheduler(),
                                label="Scheduler",
                                value=default.scheduler,
                                multiselect=True,
                                scale=4,
                            ),
                        )
                    with gr.Row():
                        with gr.Column():
                            steps_min = r(
                                "steps_min",
                                gr.Slider(
                                    1,
                                    150,
                                    step=1,
                                    value=default.steps_min,
                                    label="Min Sampling Steps",
                                ),
                            )
                            steps_max = r(
                                "steps_max",
                                gr.Slider(
                                    1,
                                    150,
                                    step=1,
                                    value=default.steps_max,
                                    label="Max Sampling Steps",
                                ),
                            )
                        with gr.Column():
                            cfg_min = r(
                                "cfg_min",
                                gr.Slider(
                                    0.1,
                                    30,
                                    step=0.1,
                                    value=default.cfg_min,
                                    label="Min CFG Scale",
                                ),
                            )
                            cfg_max = r(
                                "cfg_max",
                                gr.Slider(
                                    0.1,
                                    30,
                                    step=0.1,
                                    value=default.cfg_max,
                                    label="Max CFG Scale",
                                ),
                            )
                        with gr.Row():
                            batch_count = r(
                                "batch_count",
                                gr.Number(
                                    label="Batch Count",
                                    value=default.batch_count,
                                    precision=0,
                                ),
                            )
                            batch_size = r(
                                "batch_size",
                                gr.Number(
                                    label="Batch Size",
                                    value=default.batch_size,
                                    precision=0,
                                ),
                            )

                    size = r(
                        "size",
                        gr.Textbox(
                            label="Image Size(s) (w:h,w:h,...) (separate by commas)",
                            placeholder="e.g. 896:1152,1024:1024,1152:896",
                            value=default.size or "896:1152,1024:1024,1152:896",
                        ),
                    )
                    
                    with gr.Accordion(label="ADetailer (Simplified)", open=False):
                        adetailer = r(
                            "adetailer",
                            gr.Checkbox(
                                value=default.adetailer,
                                label="Enable ADetailer with Template",
                                info="Enable ADetailer for image generation",
                            ),
                        )
                        enable_hand_tap = r(
                            "enable_hand_tap",
                            gr.Checkbox(
                                value=default.enable_hand_tap,
                                label="Enable Hand Restoration",
                                info="Enable hand_yolov8s.pt detector",
                            ),
                        )
                        disable_lora_in_adetailer = r(
                            "disable_lora_in_adetailer",
                            gr.Checkbox(
                                value=default.disable_lora_in_adetailer,
                                label="Disable LoRA Trigger in ADetailer",
                                info="If enabled, LoRA trigger (<lora:name:.0>) will not be applied in ADetailer",
                            ),
                        )
                    with gr.Accordion(
                        label="FreeU (Integrated for ForgeUI)", open=False
                    ):
                        enable_freeu = r(
                            "enable_freeu",
                            gr.Checkbox(
                                value=default.enable_freeu,
                                label="Enable FreeU",
                                info="Enable FreeU for image generation",
                            ),
                        )
                        freeu_preset = r(
                            "freeu_preset",
                            gr.Dropdown(
                                choices=["SDXL", "SD 1.X"],
                                label="FreeU Preset",
                                value=default.freeu_preset,
                            ),
                        )
                    
                    with gr.Accordion(
                        label="SelfAttentionGuidance (Integrated for ForgeUI)", open=False
                    ):
                        enable_sag = r(
                            "enable_sag",
                            gr.Checkbox(
                                value=default.enable_sag,
                                label="Enable SelfAttentionGuidance",
                                info="Enable SelfAttentionGuidance for image generation",
                            ),
                        )
                        sag_strength = r(
                            "sag_strength",
                            gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                step=0.01,
                                label="SelfAttentionGuidance Strength",
                                value=default.sag_strength,
                            ),
                        )
                        
            with gr.Row():
                with gr.Accordion(label="Advanced Options", open=False):
                    with gr.Row():
                        save_tmp_images = r(
                            "save_tmp_images",
                            gr.Checkbox(
                                label="Save Temporary Images",
                                value=default.save_tmp_images,
                                info="Enable saving of temporary images (./tmp/img/..)",
                            )
                        )
                        prompt_generation_max_tries = r(
                            "prompt_generation_max_tries",
                            gr.Number(
                                label="Prompt Generation Max Tries",
                                value=default.prompt_generation_max_tries or 500000,
                            )
                        )
                    with gr.Row():
                        with gr.Column():
                            booru_filter_enable = r(
                                "booru_filter_enable",
                                gr.Checkbox(
                                    value=default.booru_filter_enable,
                                    label="Enable Caption Filter",
                                ),
                            )
                            booru_use_shared = r(
                                "booru_use_shared",
                                gr.Checkbox(
                                    value=default.booru_use_shared,
                                    label="Use Shared Instance",
                                    info="Use shared instance for VRAM saving"
                                ),
                            )
                        
                        booru_model = r(
                            "booru_model",
                            gr.Dropdown(
                                choices=[
                                    x["display_name"]
                                    for x in shared.models["wd-tagger"]
                                ],  # TODO: wd以外のtaggerからも取得するように
                                value=default.booru_model,
                                label="Tagger Model",
                            ),
                        )
                    
                    with gr.Group():
                        with gr.Row():
                            enable_auto_stop = r(
                                "enable_auto_stop",
                                gr.Checkbox(
                                    label="Enable Auto-Stop",
                                    value=default.enable_auto_stop,
                                    info="Enable stop generation after options",
                                ),
                            )
                            stop_mode = r(
                                "stop_mode",
                                gr.Dropdown(
                                    choices=[
                                        "After Minutes",
                                        "After Images",
                                        "At Datetime",
                                    ],
                                    value=default.stop_mode or "After Minutes",
                                    label="Stop Mode",
                                ),
                            )
                        with gr.Row():
                            stop_minutes = r(
                                "stop_minutes",
                                gr.Number(
                                    label="Stop After Minutes",
                                    value=default.stop_minutes or 240,
                                    precision=0,
                                    step=1,
                                ),
                            )
                            stop_after_img = r(
                                "stop_after_img",
                                gr.Number(
                                    label="Stop After n of Images",
                                    value=default.stop_after_img or 0,
                                    precision=0,
                                    step=1,
                                ),
                            )
                            stop_after_datetime = r(
                                "stop_after_datetime",
                                gr.Textbox(
                                    label="Stop At Datetime",
                                    value=default.stop_after_datetime
                                    or "2025-07-24 00:07:24",
                                    placeholder="YYYY-MM-DD HH:MM:SS",
                                ),
                            )
                    
                    with gr.Row():
                        enable_neveroom_unet = r(
                            "enable_neveroom_unet",
                            gr.Checkbox(
                                label="Enable NeverOOM (UNet)",
                                value=default.enable_neveroom_unet,
                                info="Enable NeverOOM / UNet Integration",
                            ),
                        )
                        enable_neveroom_vae = r(
                            "enable_neveroom_vae",
                            gr.Checkbox(
                                label="Enable NeverOOM (VAE)",
                                value=default.enable_neveroom_vae,
                                info="Enable NeverOOM / VAE Integration",
                            ),
                        )
                
                with gr.Accordion(label="Output Options", open=False):
                    with gr.Row():
                        output_dir = r(
                            "output_dir",
                            gr.Textbox(
                                label="Output Directory",
                                placeholder="Enter the output directory",
                                value=default.output_dir
                                or os.path.join(
                                    shared.api_path, "outputs/txt2img-images/{DATE}-pem"
                                ),
                                lines=1,
                                max_lines=1,
                                scale=19,
                            ),
                        )
                        browse_dir = gr.Button("📁", variant="secondary", scale=1)
                        browse_dir.click(fn=select_folder, outputs=[output_dir])
                    with gr.Row():
                        output_format = r(
                            "output_format",
                            gr.Dropdown(
                                choices=["PNG", "JPEG", "WEBP"],
                                label="Output Format",
                                value=default.output_format or "PNG",
                                scale=6,
                            ),
                        )
                        output_name = r(
                            "output_name",
                            gr.Textbox(
                                label="Output Name",
                                placeholder="Enter the output name",
                                value=default.output_name
                                or "{image_count}-{seed}.{ext}",
                                lines=1,
                                max_lines=1,
                                scale=4,
                            ),
                        )
                    with gr.Row():
                        save_metadata = r(
                            "save_metadata",
                            gr.Checkbox(
                                value=default.save_metadata,
                                label="Save Metadata",
                                info="If enabled, metadata will be saved in the output image",
                            ),
                        )
                        save_infotext = r(
                            "save_infotext",
                            gr.Checkbox(
                                value=default.save_infotext,
                                label="Save Infotext",
                                info="If enabled, infotext will be saved as .txt",
                            ),
                        )
                
            with gr.Row():
                with gr.Column(scale=6):
                    with gr.Row():
                        update_blacklist = gr.Button(
                            "Update Prompt setting",
                            variant="secondary",
                        )
                        skip_img = gr.Button("Skip Image", variant="secondary")
                skipped_img = gr.Checkbox(
                    value=False,
                    label="Skipped",
                    interactive=False,
                    scale=2
                )
                stopping_gen = gr.Checkbox(
                    value=False,
                    label="Stopping Generation",
                    interactive=False,
                    scale=2
                )
                skip_img.click(fn=instance.skip_image, inputs=[], outputs=[skipped_img])

            with gr.Blocks():
                with gr.Row():
                    generate = gr.Button("Start", elem_classes=["green-button"])
                    stop = gr.Button("Stop", elem_classes=["red-button"],variant="stop")
                with gr.Row():
                    with gr.Column():
                        eta = gr.Textbox(
                            label="ETA",
                            placeholder="Estimated time of arrival",
                            lines=1,
                            max_lines=1,
                            value="",
                            scale=2,
                            interactive=False,
                        )
                        output = gr.Textbox(
                            label="Logs",
                            placeholder="",
                            lines=12,
                            max_lines=24,
                            value="",
                            scale=3,
                        )

                    with gr.Column():
                        progress_bar_html = gr.HTML(
                            label="Progress Bar",
                            value="<div style='width: 100%; height: 20px; background-color: #f3f3f3; border-radius: 5px;'><div style='width: 0%; height: 100%; background-color: #4caf50; border-radius: 5px;'></div></div>",
                        )
                        image = gr.Image(
                            label="Generated Image", type="pil", scale=3, interactive=False
                        )
            var = [
                header,
                footer,
                tags,
                random_rate,
                add_lora_name,
                s_method,
                scheduler,
                steps_min,
                steps_max,
                cfg_min,
                cfg_max,
                batch_count,
                batch_size,
                size,
                adetailer,
                enable_hand_tap,
                disable_lora_in_adetailer,
                enable_freeu,
                freeu_preset,
                negative,
                enable_sag,
                sag_strength,
                use_images,
                use_folder,
                tag_count_weight,
                remove_character,
                save_tmp_images,
                prompt_generation_max_tries,
                prompt_weight_chance,
                prompt_weight_min,
                prompt_weight_max,
                instance_blacklist,
                output_dir,
                output_format,
                output_name,
                save_metadata,
                save_infotext,
                booru_filter_enable,
                booru_use_shared,
                booru_model,
                enable_neveroom_unet,
                enable_neveroom_vae,
                enable_auto_stop,
                stop_mode,
                stop_minutes,
                stop_after_img,
                stop_after_datetime,
            ]
            save_all_param = gr.Button("Save current parameters", variant="secondary")
            save_all_param.click(
                fn=forever_generation_from_images.insta_save,
                inputs=forever_generation_from_images.values(),
                outputs=[],
            )
            
            generate.click(
                fn=instance.start,
                inputs=var,
                outputs=[eta, progress_bar_html, image, output, skipped_img, stopping_gen],
            )
            stop.click(fn=instance.stop_generation, inputs=[], outputs=[])