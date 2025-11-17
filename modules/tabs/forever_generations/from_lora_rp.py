from modules.utils.lora_util import list_lora_with_tags
from modules.utils.browse import select_folder
from modules.api.v1.items import sdapi
from webui import UiTabs
from modules.utils.ui.register import RegisterComponent
from pathlib import Path

import gradio as gr
import os
import shared

class FromLoRARegionalPrompter(UiTabs):
    def title(self):
        return "From LoRA (RP)"

    def index(self):
        return 2

    async def ui(self, outlet):
        forever_generation_from_lora = RegisterComponent(
            Path("./defaults/forever_generation.from_lora_rp.json"),
            "forever_generations/from_lora_rp",
        )
        r = forever_generation_from_lora.register
        default = forever_generation_from_lora.get()
        
        prompt_setting_generations = [
            "Base", "A", "B",
        ]
        prompt_setting_base = []
        prompt_setting_a = []
        prompt_setting_b = []
        
        with gr.Blocks():
            def create_prompt_setting(discriminator):
                d = "_" + discriminator.lower()
                elements = []
                with gr.Accordion(label="Prompt Settings", open=False):
                    with gr.Row():
                        max_tags = r(
                            f"max_tags" + d,
                            gr.Number(
                                label="Max tags",
                                value=getattr(default, "max_tags" + d),
                                precision=0,
                                scale=3,
                            ),
                        )
                        elements.append(max_tags)

                        base_chance = r(
                            "base_chance" + d,
                            gr.Slider(
                                0.01,
                                10,
                                step=0.01,
                                value=getattr(default, "base_chance" + d),
                                label="Base chance",
                                info="Base chance for the tag to be included in the prompt",
                                scale=4,
                            ),
                        )
                        elements.append(base_chance)

                    with gr.Row():
                        add_lora_name = r(
                            "add_lora_name" + d,
                            gr.Checkbox(
                                value=getattr(default, "add_lora_name" + d),
                                label="Add LoRA name to prompt",
                                info="If enabled, the LoRA name will be added to the prompt",
                                scale=2,
                            ),
                        )
                        elements.append(add_lora_name)

                        lora_weight = r(
                            "lora_weight" + d,
                            gr.Textbox(
                                label="LoRA weight",
                                placeholder="lbw=OUTALL:stop=20",
                                value=str(getattr(default, "lora_weight" + d))
                                if getattr(default, "lora_weight" + d)
                                else "0.5",
                                lines=1,
                                max_lines=1,
                                scale=2,
                            ),
                        )
                        elements.append(lora_weight)

                    header = r(
                        "header" + d,
                        gr.Textbox(
                            label="Prompt Header",
                            placeholder="Enter the prompt header",
                            lines=2,
                            max_lines=5,
                            value=getattr(default, "header" + d),
                        ),
                    )
                    elements.append(header)

                    footer = r(
                        "footer" + d,
                        gr.Textbox(
                            label="Prompt Footer",
                            placeholder="Enter the prompt footer",
                            lines=2,
                            max_lines=5,
                            value=getattr(default, "footer" + d),
                        ),
                    )
                    elements.append(footer)

                    with gr.Row():
                        prompt_weight_chance = r(
                            "prompt_weight_chance" + d,
                            gr.Slider(
                                0,
                                1,
                                label="Add prompt weight change",
                                info="0 to disable",
                                value=getattr(default, "prompt_weight_chance" + d),
                                step=0.01,
                            ),
                        )
                        elements.append(prompt_weight_chance)

                        with gr.Column():
                            prompt_weight_min = r(
                                "prompt_weight_min" + d,
                                gr.Slider(
                                    0,
                                    2,
                                    step=0.01,
                                    value=getattr(default, "prompt_weight_min" + d),
                                    label="Prompt weight min",
                                    info="Minimum prompt weight",
                                ),
                            )
                            elements.append(prompt_weight_min)

                            prompt_weight_max = r(
                                "prompt_weight_max" + d,
                                gr.Slider(
                                    0,
                                    2,
                                    step=0.01,
                                    value=getattr(default, "prompt_weight_max" + d),
                                    label="Prompt weight max",
                                    info="Maximum prompt weight",
                                ),
                            )
                            elements.append(prompt_weight_max)

                    with gr.Row():
                        remove_character = r(
                            "remove_character" + d,
                            gr.Checkbox(
                                value=getattr(default, "remove_character" + d),
                                label="Remove additional character tags",
                            ),
                        )
                        elements.append(remove_character)

                return elements
            
            def on_lora_change(lora, enable):
                df = len(lora) <= 1
                return (
                    gr.Checkbox(
                        value=False if df else enable,
                        interactive=not df
                    ),
                    gr.Slider(
                        interactive=not df and enable,
                        maximum=len(lora)
                    )
                )
            
            var = []
            lora_choices = list_lora_with_tags()
            with gr.Row():
                with gr.Accordion("P.opt (Base)", open=True):
                    prompt_setting_base = []
                    base_lora = r(
                        "base_lora",
                        gr.Dropdown(
                            choices=lora_choices,
                            multiselect=True,
                            value=default.base_lora,
                            label="Target LoRA",
                            scale=8,
                        ),
                    )
                    with gr.Row():
                        base_random_lora_toggle = r(
                            "base_random_lora_toggle",
                            gr.Checkbox(
                                value=default.base_random_lora_toggle,
                                label="Random LoRA Selection",
                                info="Randomly select one LoRA from the list for each generation",
                                scale=2,
                            ),
                        )
                        base_rnd_lora_select_count = r(
                            "base_rnd_lora_select_count",
                            gr.Slider(
                                1, 100, step=1, value=default.base_rnd_lora_select_count,
                                interactive=default.base_erl,
                            ),
                        )
                        
                    base_lora.change(
                        fn=on_lora_change,
                        inputs=[base_lora, base_random_lora_toggle],
                        outputs=[base_random_lora_toggle, base_rnd_lora_select_count],
                        show_progress=False
                    )
                    prompt_setting_base.extend(
                        [
                            base_lora,
                            base_random_lora_toggle,
                            base_rnd_lora_select_count,
                        ]
                    )
                    prompt_setting_base.extend(create_prompt_setting("Base"))
                
                with gr.Accordion("P.opt (A)", open=True):
                    prompt_setting_a = []
                    a_lora = r(
                        "a_lora",
                        gr.Dropdown(
                            choices=lora_choices,
                            multiselect=True,
                            value=getattr(default, "a_lora", []),
                            label="Target LoRA",
                            scale=8,
                        ),
                    )
                    with gr.Row():
                        a_random_lora_toggle = r(
                            "a_random_lora_toggle",
                            gr.Checkbox(
                                value=getattr(default, "a_random_lora_toggle", False),
                                label="Random LoRA Selection",
                                info="Randomly select one LoRA from the list for each generation",
                                scale=2,
                            ),
                        )
                        a_rnd_lora_select_count = r(
                            "a_rnd_lora_select_count",
                            gr.Slider(
                                1,
                                100,
                                step=1,
                                value=getattr(default, "a_rnd_lora_select_count", 1),
                                interactive=getattr(default, "a_erl", False),
                            ),
                        )
                    a_lora.change(
                        fn=on_lora_change,
                        inputs=[a_lora, a_random_lora_toggle],
                        outputs=[a_random_lora_toggle, a_rnd_lora_select_count],
                        show_progress=False,
                    )
                    prompt_setting_a.extend(
                        [
                            a_lora,
                            a_random_lora_toggle,
                            a_rnd_lora_select_count,
                        ]
                    )
                    prompt_setting_a.extend(create_prompt_setting("A"))
                
                with gr.Accordion("P.opt (B)", open=True):
                    prompt_setting_b = []
                    b_lora = r(
                        "b_lora",
                        gr.Dropdown(
                            choices=lora_choices,
                            multiselect=True,
                            value=getattr(default, "b_lora", []),
                            label="Target LoRA",
                            scale=8,
                        ),
                    )
                    with gr.Row():
                        b_random_lora_toggle = r(
                            "b_random_lora_toggle",
                            gr.Checkbox(
                                value=getattr(default, "b_random_lora_toggle", False),
                                label="Random LoRA Selection",
                                info="Randomly select one LoRA from the list for each generation",
                                scale=2,
                            ),
                        )
                        b_rnd_lora_select_count = r(
                            "b_rnd_lora_select_count",
                            gr.Slider(
                                1,
                                100,
                                step=1,
                                value=getattr(default, "b_rnd_lora_select_count", 1),
                                interactive=getattr(default, "b_erl", False),
                            ),
                        )
                        
                    b_lora.change(
                        fn=on_lora_change,
                        inputs=[b_lora, b_random_lora_toggle],
                        outputs=[b_random_lora_toggle, b_rnd_lora_select_count],
                        show_progress=False,
                    )
                    prompt_setting_b.extend(
                        [
                            b_lora,
                            b_random_lora_toggle,
                            b_rnd_lora_select_count,
                        ]
                    )
                    prompt_setting_b.extend(create_prompt_setting("B"))
                
                var += prompt_setting_base + prompt_setting_a + prompt_setting_b
            
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
                with gr.Accordion(label="Parameter Settings", open=False):
                        with gr.Row():
                            s_method = r(
                                "s_method",
                                gr.Dropdown(
                                    choices=(await sdapi.get_samplers())[0],
                                    label="Sampling Methods",
                                    value=default.s_method,
                                    multiselect=True,
                                    scale=6,
                                ),
                            )
                            scheduler = r(
                                "scheduler",
                                gr.Dropdown(
                                    choices=(await sdapi.get_schedulers())[0],
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
                            preset = r(
                                "preset",
                                gr.Dropdown(
                                    choices=["SDXL", "SD 1.X"],
                                    label="FreeU Preset",
                                    value=default.preset,
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
                
                with gr.Accordion(label="Regional Prompter"):
                    pass
            
            with gr.Row():
                with gr.Accordion(label="Advanced Settings", open=False):
                        with gr.Group():
                            with gr.Row():
                                enable_stop = r(
                                    "enable_stop",
                                    gr.Checkbox(
                                        label="Enable Auto-Stop",
                                        value=default.enable_stop,
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
                                stop_after_minutes = r(
                                    "stop_after_minutes",
                                    gr.Number(
                                        label="Stop After Minutes",
                                        value=default.stop_after_minutes or 240,
                                        precision=0,
                                        step=1,
                                    ),
                                )
                                stop_after_images = r(
                                    "stop_after_images",
                                    gr.Number(
                                        label="Stop After n of Images",
                                        value=default.stop_after_images or 0,
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
                            booru_filter_enable = r(
                                "booru_filter_enable",
                                gr.Checkbox(
                                    value=default.booru_filter_enable,
                                    label="Enable Caption Filter",
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
                        
                        
                with gr.Row():
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
                
            var += [
                negative,

                # Parameter Settings
                s_method,
                scheduler,
                steps_min,
                steps_max,
                cfg_min,
                cfg_max,
                batch_count,
                batch_size,
                size,

                # ADetailer / FreeU / SAG
                adetailer,
                enable_hand_tap,
                disable_lora_in_adetailer,
                enable_freeu,
                preset,
                enable_sag,
                sag_strength,

                # Advanced Settings
                enable_stop,
                stop_mode,
                stop_after_minutes,
                stop_after_images,
                stop_after_datetime,
                save_tmp_images,
                prompt_generation_max_tries,
                booru_filter_enable,
                booru_model,
                enable_neveroom_unet,
                enable_neveroom_vae,

                # Output Options (browse button is not registered)
                output_dir,
                output_format,
                output_name,
                save_metadata,
                save_infotext,
            ]