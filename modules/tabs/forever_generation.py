import os
from pathlib import Path
import gradio as gr
from typing import Callable

from logger import critical, debug, println
from modules.sd_param import get_sampler, get_scheduler
from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent, rcMap
import shared
from webui import UiTabs


class Define(UiTabs):
    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "forever_generations")

    def title(self) -> str:
        return "Forever Image Generation"

    def index(self) -> int:
        return 0

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        forever_generation = RegisterComponent(
            Path("./defaults/forever_generation.common.json"),
            "forever_generation/common",
        )
        r = forever_generation
        pmgr = forever_generation.pmgr
        default = forever_generation.get()
        current_tab_str = "from LoRA"
        
    
        with gr.Blocks():
            tabs = await super().ui(outlet)
            all_components = []
            all_rc = {}
            components_index = {}
            
            for key in rcMap.keys():
                if key == "forever_generation/common": continue
                if not key.startswith("forever_generation/"): continue
                rc = RegisterComponent.get_rc(key)
                si = len(all_components)
                to_add = rc.values()
                if len(to_add) == 0: 
                    critical(f"No components registered for {key}!")
                    continue
                all_components.extend(to_add)
                ei = len(all_components)-1
                all_rc[key.replace("forever_generation/", "")] = rc
                components_index[key.replace("forever_generation/", "")] = (si, ei)
            
            def slice_args(current_tab, args):
                if current_tab not in components_index:
                    raise gr.Error(f"No components data found for the current tab. ({current_tab})")
                target_index = components_index[current_tab]
                rc = all_rc[current_tab]
                base_count = len(forever_generation.keys()) 
                
                # slice args
                base = args[:base_count]
                tab_args = args[target_index[0]+base_count:target_index[1]+1+base_count]
                kw = dict(zip(
                    forever_generation.keys() + rc.keys(), 
                    base+tab_args
                ))
                return (kw, base, tab_args)

            async def start_generation(*args):
                current_tab = current_tab_str.replace(" ", "_").lower()
                
                println(f"Starting generation: {current_tab})")
                println(shared.fv_instances)
                kw = slice_args(current_tab, args)[0]
                debug(f"Generation params: {kw}")
                if current_tab in shared.fv_instances.keys():
                    async for r in shared.fv_instances[current_tab].start(**kw):
                        yield r
                else:
                    raise gr.Error(f"No instance found for the current tab. ({current_tab})")
            
            async def skip_image():
                current_tab = current_tab_str.replace(" ", "_").lower()
                if current_tab in shared.fv_instances.keys():
                    return await shared.fv_instances[current_tab].skip_image()
            
            async def stop_generation():
                current_tab = current_tab_str.replace(" ", "_").lower()
                if current_tab in shared.fv_instances.keys():
                    return await shared.fv_instances[current_tab].stop_generation()
            
            async def update_prompt_settings(*args):
                current_tab = current_tab_str.replace(" ", "_").lower()
                println(f"updating param: {current_tab})")
                println(shared.fv_instances)
                kw = slice_args(current_tab, args)[0]
                # print(forever_generation.keys())
                if current_tab in shared.fv_instances.keys():
                    async for r in await shared.fv_instances[current_tab].update_prompt_settings(**kw):
                        yield r
                else:
                    raise gr.Error(f"No instance found for the current tab. ({current_tab})")
            
            async def load_param(name):
                current_tab = current_tab_str.replace(" ", "_").lower()
                pmgr = all_rc[current_tab].pmgr
                if name not in pmgr.list_presets():
                    raise gr.Error(f"Preset '{name}' not found for the current tab. ({current_tab})")
                target_index = components_index[current_tab]
                
        
            # current_tab_str = "from_lora"
            current_tab = gr.State(value="from LoRA")
            def upd_ctab(evt: gr.SelectData):
                nonlocal current_tab_str; current_tab_str = evt.value
                return evt.value
            tabs.select(upd_ctab, show_progress=False, outputs=current_tab)
            
                
            with gr.Accordion("", open=True):
                with gr.Row():
                    with gr.Accordion(label="Prompt Settings", open=False):
                        with gr.Row():
                            tags = r(
                                "tags",
                                gr.Number(
                                    label="Max tags",
                                    value=default.tags,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            random_rate = r(
                                "random_rate",
                                gr.Slider(
                                    0.01,
                                    10,
                                    step=0.01,
                                    value=default.random_rate,
                                    label="Random rate",
                                    info="Rate at which tags are randomly included in the prompt",
                                    scale=4,
                                ),
                            )
                        with gr.Row():
                            add_lora_name = r(
                                "add_lora_name",
                                gr.Checkbox(
                                    value=default.add_lora_name,
                                    label="Add LoRA name to prompt",
                                    info="If enabled, the LoRA name will be added to the prompt",
                                    scale=1,
                                ),
                            )
                            add_trigger_word = r(
                                "add_trigger_word",
                                gr.Checkbox(
                                    value=default.add_trigger_word,
                                    label="Add LoRA trigger to prompt",
                                    info="If enabled, the trigger word (lorajson) will be added to the prompt",
                                    scale=1,
                                ),
                            )
                            add_trig_to = r(
                                "add_trig_to",
                                gr.Dropdown(
                                    multiselect=True,
                                    label="Add trigger to",
                                    choices=["positive", "negative"],
                                    value=default.add_trig_to,
                                ),
                            )

                        with gr.Row():
                            lora_weight = r(
                                "lora_weight",
                                gr.Textbox(
                                    label="LoRA weight",
                                    placeholder="lbw=OUTALL:stop=20",
                                    value=str(default.lora_weight) if default.lora_weight else "0.5",
                                    lines=1,
                                    max_lines=1,
                                    scale=2,
                                ),
                            )
                            lora_weight_prio = r(
                                "lora_weight_prio",
                                gr.Radio(
                                    choices=["lorainfo", "setting"],
                                    value=default.lora_weight_prio,
                                    label="LoRA weight src priority",
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
                                    0,
                                    1,
                                    label="Add prompt weight change",
                                    info="0 to disable",
                                    value=default.prompt_weight_chance,
                                    step=0.01,
                                ),
                            )
                            with gr.Column():
                                prompt_weight_min = r(
                                    "prompt_weight_min",
                                    gr.Slider(
                                        0,
                                        2,
                                        step=0.01,
                                        value=default.prompt_weight_min,
                                        label="Prompt weight min",
                                        info="Minimum prompt weight",
                                    ),
                                )
                                prompt_weight_max = r(
                                    "prompt_weight_max",
                                    gr.Slider(
                                        0,
                                        2,
                                        step=0.01,
                                        value=default.prompt_weight_max,
                                        label="Prompt weight max",
                                        info="Maximum prompt weight",
                                    ),
                                )
                        with gr.Row():
                            remove_character = r(
                                "remove_character",
                                gr.Checkbox(
                                    value=default.remove_character,
                                    label="Remove additional character tags",
                                ),
                            )

                        blacklist = r(
                            "blacklist",
                            gr.Textbox(
                                label="Instance Blacklist",
                                placeholder="Enter regex patterns (comma separated)",
                                value=default.blacklist,
                                lines=2,
                                max_lines=5,
                                info="applied only to that run.",
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
                        with gr.Accordion(label="FreeU (Integrated for ForgeUI)", open=False):
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

                    with gr.Accordion(label="Advanced Settings", open=False):
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
                                        value=default.stop_after_datetime or "2025-07-24 00:07:24",
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
                                ),
                            )
                            prompt_generation_max_tries = r(
                                "prompt_generation_max_tries",
                                gr.Number(
                                    label="Prompt Generation Max Tries",
                                    value=default.prompt_generation_max_tries or 500000,
                                ),
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
                                        info="Use shared instance for VRAM saving",
                                    ),
                                )

                            booru_model = r(
                                "booru_model",
                                gr.Dropdown(
                                    choices=[x["display_name"] for x in shared.models["wd-tagger"]],
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

                        with gr.Accordion(label="Experimental", open=False):
                            merge_adetailer_test = r(
                                "merge_adetailer_test",
                                gr.Checkbox(
                                    label="Merge ADetailer Test (Experimental)",
                                    value=default.merge_adetailer_test or False,
                                    info="Merge ADetailer into the main generation process (Experimental)",
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
                                    or os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem"),
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
                                    value=default.output_name or "{image_count}-{seed}.{ext}",
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
                            update_psettings = gr.Button(
                                "Update Base setting",
                                variant="secondary",
                                scale=2,
                            )
                            skip_img = gr.Button("Skip Image", variant="secondary", scale=3)
                    skipped_img = gr.Checkbox(
                        value=False,
                        label="Skipped",
                        interactive=False,
                        scale=2,
                    )
                    stopped_generation = gr.Checkbox(
                        value=False,
                        label="Stopped",
                        interactive=False,
                        scale=2,
                    )
                    update_psettings.click(
                        fn=update_prompt_settings,
                        inputs=forever_generation.values() + [current_tab],
                        outputs=[],
                    )
                    skip_img.click(fn=skip_image, inputs=[], outputs=[skipped_img])

                with gr.Blocks():
                    with gr.Row():
                        generate = gr.Button("Start", elem_classes=["green-button"])
                        stop = gr.Button("Stop", elem_classes=["red-button"], variant="stop")
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
                    
                    with gr.Row():
                        preset_name = gr.Dropdown(
                            choices=pmgr.list_presets(),
                            label="Presets (type to create new)",
                            value=pmgr.current_preset,
                            scale=9,
                            allow_custom_value=True
                        )
                        rld_preset = gr.Button("Reload", variant="secondary", scale=1)
                        rld_preset.click(
                            lambda: gr.Dropdown(choices=pmgr.list_presets()),
                            outputs=preset_name,
                            show_progress=False,
                        )
                    
                    load_all_param = gr.Button("Load preset", variant="secondary", size="sm")
                    save_all_param = gr.Button("Save current parameters", variant="secondary")
                
                generate.click(
                    start_generation, 
                    inputs=forever_generation.values() + all_components + [current_tab],
                    outputs=[eta, progress_bar_html, image, output, skipped_img, stopped_generation],
                )
                stop.click(fn=stop_generation)