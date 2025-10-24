from modules.forever.from_lora import ForeverGenerationFromLoRA
from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent
from modules.utils.lora_util import list_lora_with_tags
from modules.api.v1.items import sdapi
from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *
from pathlib import Path


class LoRAToPrompt(UiTabs):
    def title(self) -> str:
        return "from LoRA"

    def index(self) -> int:
        return 1

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        instance = ForeverGenerationFromLoRA()
        forever_generation_from_lora = RegisterComponent(
            Path("./defaults/forever_generation.from_lora.json"),
            "forever_generations/from_lora",
        )
        r = forever_generation_from_lora.register
        default = forever_generation_from_lora.get()

        with gr.Blocks():
            with gr.Group():
                lora = r(
                    "lora",
                    gr.Dropdown(
                        choices=list_lora_with_tags(),
                        multiselect=True,
                        value=default.lora,
                        label="Target LoRA",
                        scale=8,
                    ),
                )
                with gr.Row():
                    enable_random_lora = r(
                        "enable_random_lora",
                        gr.Checkbox(
                            value=default.enable_random_lora,
                            label="Random LoRA Selection",
                            info="Randomly select one LoRA from the list for each generation",
                            scale=2,
                        ),
                    )
                    rnd_lora_select_count = r(
                        "rnd_lora_select_count",
                        gr.Slider(
                            1, 100, step=1, value=default.rnd_lora_select_count,
                            interactive=default.enable_random_lora,
                        ),
                    )
                
            with gr.Row():
                with gr.Accordion(label="Prompt Settings", open=False):
                    with gr.Row():
                        max_tags = r(
                            "max_tags",
                            gr.Number(
                                label="Max tags",
                                value=default.max_tags,
                                precision=0,
                                scale=3,
                            ),
                        )
                        base_chance = r(
                            "base_chance",
                            gr.Slider(
                                0.01,
                                10,
                                step=0.01,
                                value=default.base_chance,
                                label="Base chance",
                                info="Base chance for the tag to be included in the prompt",
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
                                scale=2,
                            ),
                        )
                        lora_weight = r(
                            "lora_weight",
                            gr.Textbox(
                            label="LoRA weight",
                            placeholder="lbw=OUTALL:stop=20",
                            value=str(default.lora_weight) if default.lora_weight else "0.5", lines=1, max_lines=1, scale=2
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
                    
            with gr.Row():
                with gr.Accordion(label="Image Filtering", open=False):
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
                    with gr.Row():
                        booru_threshold = r(
                            "booru_threshold",
                            gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=default.booru_threshold or 0.65,
                                label="Caption Filter Threshold",
                                step=0.01,
                                info="Threshold for the caption filter",
                            ),
                        )
                        booru_character_threshold = r(
                            "booru_character_threshold",
                            gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=default.booru_character_threshold or 0.45,
                                label="Character Filter Threshold",
                                step=0.01,
                                info="Threshold for the character filter",
                            ),
                        )
                    with gr.Row():
                        booru_allow_rating = r(
                            "booru_allow_rating",
                            gr.Dropdown(
                                choices=[
                                    "general",
                                    "sensitive",
                                    "questionable",
                                    "explicit",
                                ],
                                value=default.booru_allow_rating
                                or ["general", "sensitive", "questionable", "explicit"],
                                multiselect=True,
                                label="[wip] Allow Ratings",
                                scale=6,
                            ),
                        )
                        booru_ignore_questionable = r(
                            "booru_ignore_questionable",
                            gr.Checkbox(
                                value=default.booru_ignore_questionable,
                                label="Ignore Questionable",
                                info="If enabled, questionable weight will be ignored (questionable 99%, sensitive 1% will be treated as sensitive 100%)",
                                scale=4,
                            ),
                        )

                    with gr.Accordion(label="Save Option", open=False):

                        def set_visible_from_rating(allow_rate):
                            g = "general" in allow_rate
                            s = "sensitive" in allow_rate
                            q = "questionable" in allow_rate
                            e = "explicit" in allow_rate
                            return (
                                gr.update(visible=g),
                                gr.update(visible=s),
                                gr.update(visible=q),
                                gr.update(visible=e),
                            )

                        with gr.Row():
                            booru_save_each_rate = r(
                                "booru_save_each_rate",
                                gr.Checkbox(
                                    value=default.booru_save_each_rate,
                                    label="Save Each Rating",
                                ),
                            )

                            booru_merge_sensitive = r(
                                "booru_merge_sensitive",
                                gr.Checkbox(
                                    value=default.booru_merge_sensitive,
                                    label="Merge Sensitive to general",
                                ),
                            )
                        with gr.Row(visible=True) as general_row:
                            general_save_dir = r(
                                "general_save_dir",
                                gr.Textbox(
                                    label="[Rating] General Save Directory",
                                    placeholder="Enter the general save directory",
                                    value=default.general_save_dir
                                    or os.path.join(
                                        shared.api_path,
                                        "outputs/txt2img-images/{DATE}-pem/general",
                                    ),
                                    lines=1,
                                    max_lines=1,
                                    scale=19,
                                ),
                            )
                            general_browse_dir = gr.Button(
                                "📁", variant="secondary", scale=1
                            )
                            general_browse_dir.click(
                                fn=select_folder, outputs=[general_save_dir]
                            )
                        with gr.Row(visible=True) as sensitive_row:
                            sensitive_save_dir = r(
                                "sensitive_save_dir",
                                gr.Textbox(
                                    label="[Rating] Sensitive Save Directory",
                                    placeholder="Enter the sensitive save directory",
                                    value=default.sensitive_save_dir
                                    or os.path.join(
                                        shared.api_path,
                                        "outputs/txt2img-images/{DATE}-pem/sensitive",
                                    ),
                                    lines=1,
                                    max_lines=1,
                                    scale=19,
                                ),
                            )
                            sensitive_browse_dir = gr.Button(
                                "📁", variant="secondary", scale=1
                            )
                            sensitive_browse_dir.click(
                                fn=select_folder, outputs=[sensitive_save_dir]
                            )

                        with gr.Row(visible=True) as questionable_row:
                            questionable_save_dir = r(
                                "questionable_save_dir",
                                gr.Textbox(
                                    label="[Rating] Questionable Save Directory",
                                    placeholder="Enter the questionable save directory",
                                    value=default.questionable_save_dir
                                    or os.path.join(
                                        shared.api_path,
                                        "outputs/txt2img-images/{DATE}-pem/questionable",
                                    ),
                                    lines=1,
                                    max_lines=1,
                                    scale=19,
                                ),
                            )
                            questionable_browse_dir = gr.Button(
                                "📁", variant="secondary", scale=1
                            )
                            questionable_browse_dir.click(
                                fn=select_folder, outputs=[questionable_save_dir]
                            )

                        with gr.Row(visible=True) as explicit_row:
                            explicit_save_dir = r(
                                "explicit_save_dir",
                                gr.Textbox(
                                    label="[Rating] Explicit Save Directory",
                                    placeholder="Enter the explicit save directory",
                                    value=default.explicit_save_dir
                                    or os.path.join(
                                        shared.api_path,
                                        "outputs/txt2img-images/{DATE}-pem/explicit",
                                    ),
                                    lines=1,
                                    max_lines=1,
                                    scale=19,
                                ),
                            )
                            explicit_browse_dir = gr.Button(
                                "📁", variant="secondary", scale=1
                            )
                            explicit_browse_dir.click(
                                fn=select_folder, outputs=[explicit_save_dir]
                            )

                        booru_allow_rating.change(
                            fn=set_visible_from_rating,
                            inputs=[booru_allow_rating],
                            outputs=[
                                general_row,
                                sensitive_row,
                                questionable_row,
                                explicit_row,
                            ],
                        )
                    with gr.Row():
                        booru_blacklist = r(
                            "booru_blacklist",
                            gr.Textbox(
                                label="Caption Blacklist",
                                placeholder="Enter caption tags to blacklist, separated by commas",
                                info="if this tag is in the caption, the image will be skipped (or saved at other directory if enabled)",
                                lines=5,
                                max_lines=400,
                                value=default.booru_blacklist or "",
                                scale=6,
                            ),
                        )
                        booru_pattern_blacklist = r(
                            "booru_pattern_blacklist",
                            gr.Textbox(
                                label="Caption Blacklist Patterns",
                                placeholder="Enter caption patterns to blacklist, separated by lines",
                                info="if this pattern matches the caption, the image will be skipped (or saved at other directory if enabled)",
                                lines=5,
                                max_lines=10000,
                                value=default.booru_pattern_blacklist or "",
                                scale=6,
                            ),
                        )
                    with gr.Row():
                        booru_separate_save = r(
                            "booru_separate_save",
                            gr.Checkbox(
                                value=default.booru_separate_save,
                                label="Blacklisted Save Option",
                                info="If enabled, blacklisted images will be saved to separate directory",
                                scale=10,
                            ),
                        )
                        booru_blacklist_save_dir = r(
                            "booru_blacklist_save_dir",
                            gr.Textbox(
                                label="Blacklisted Save Directory",
                                placeholder="Enter the blacklisted save directory",
                                value=default.booru_blacklist_save_dir
                                or os.path.join(
                                    shared.api_path,
                                    "C:/Users/luna_/Pictures/blacklisted",
                                ),
                                scale=19,
                            ),
                        )
                        booru_blacklist_browse_dir = gr.Button(
                            "📁", variant="secondary", scale=1
                        )
                        booru_blacklist_browse_dir.click(
                            fn=select_folder, outputs=[booru_blacklist_save_dir]
                        )

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

                with gr.Accordion(label="Regional Prompter", open=False):
                    with gr.Row():
                        active_rp = r(
                            "active_rp",
                            gr.Checkbox(
                                value=default.active_rp,
                                label="Enable Regional Prompter",
                            )
                        )
                        rp_mode = r(
                            "rp_mode",
                            gr.Dropdown(
                                choices=[
                                    "Matrix", "Mask", "Prompt"
                                ],
                                value=default.rp_mode or "Matrix",
                                label="[WIP] RP Mode",
                                interactive=False
                            )
                        )
                        
                        rp_calc = r(
                            "rp_calc",
                            gr.Dropdown(
                                choices=[
                                    "Attention", "Latent"
                                ],
                                value=default.rp_calc or "Attention",
                                label="RP Calculation Mode"
                        ))
                    
                    with gr.Row():
                        rp_base = r(
                            "rp_base",
                            gr.Checkbox(
                                label="Use base prompt",
                                value=default.rp_base,
                            )
                        )
                        rp_base_ratio = r(
                            "rp_base_ratio",
                            gr.Slider(
                                0.0,
                                1.0,
                                step=0.01,
                                value=default.rp_base_ratio or 0.5,
                                label="Base prompt ratio",
                                info="Ratio of the base prompt to the generated prompt",
                                scale=2,
                            ),
                        )
                    
                    with gr.Accordion(label="Base prompt setting", open=False):
                        lora_base = r(
                            "lora_base",
                            gr.Dropdown(
                                choices=list_lora_with_tags(),
                                multiselect=True,
                                value=default.lora,
                                label="Target LoRA",
                            ),
                        )
                        with gr.Row():
                            add_lora_name_base = r(
                                "add_lora_name_base",
                                gr.Checkbox(
                                    value=default.add_lora_name_base,
                                    label="Add LoRA name to prompt",
                                    info="If enabled, the LoRA name will be added to the prompt",
                                    scale=2,
                                ),
                            )
                            lora_weight_base = r(
                                "lora_weight_base",
                                gr.Slider(
                                    0,
                                    1,
                                    step=0.01,
                                    value=default.lora_weight_base,
                                    label="LoRA weight",
                                    info="Weight of the LoRA in the prompt",
                                    scale=4,
                                ),
                            )
                        header_base = r(
                            "header_base",
                            gr.Textbox(
                                label="Prompt Header",
                                placeholder="Enter the prompt header",
                                lines=2,
                                max_lines=5,
                                value=default.header_base,
                            ),
                        )
                        footer_base = r(
                            "footer_base",
                            gr.Textbox(
                                label="Prompt Footer",
                                placeholder="Enter the prompt footer",
                                lines=2,
                                max_lines=5,
                                value=default.footer_base,
                            ),
                        )
                        with gr.Row():
                            max_tags_base = r(
                                "max_tags_base",
                                gr.Number(
                                    label="Max tags",
                                    value=default.max_tags_base,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            base_chance_base = r(
                                "base_chance_base",
                                gr.Slider(
                                    0.01,
                                    10,
                                    step=0.01,
                                    value=default.base_chance_base,
                                    label="Base chance",
                                    info="Base chance for the tag to be included in the prompt",
                                    scale=4,
                                ),
                            )
                            disallow_duplicate_base = r(
                                "disallow_duplicate_base",
                                gr.Checkbox(
                                    value=default.disallow_duplicate_base,
                                    label="Disallow duplicate tags",
                                    info="If enabled, duplicate tags will not be included in the prompt",
                                ),
                            )
                    with gr.Accordion(label="Matrix Parameters", open=False, visible=True) as rp_matrix_root:
                        with gr.Row():
                            matrix_split = r(
                                "matrix_split",
                                gr.Dropdown(
                                    choices=["Columns", "Rows"],
                                    value=default.matrix_split or ["Columns"],
                                    multiselect=True,
                                    label="Splitting mode"
                                )
                            )
                            matrix_divide = r(
                                "matrix_divide",
                                gr.Textbox(
                                    label="Divide Ratio",
                                    value=default.matrix_divide or "1:1,2:3,3:2",
                                    placeholder="e.g. 896:1152,1024:1024,1152:896",
                                    info=""
                                )
                            )
                        with gr.Row():
                            matrix_canvas_res_auto = r(
                                "matrix_canvas_res_auto",
                                gr.Checkbox(
                                    value=default.matrix_canvas_res_auto,
                                    label="Auto Canvas Resolution",
                                    info="If enabled, the canvas resolution will be automatically calculated based on the image size",
                                ),
                            )
                            matrix_canvas_res = r(
                                "matrix_canvas_res",
                                gr.Textbox(
                                    label="Matrix Resolution",
                                    placeholder="Enter the canvas resolution (width:height)",
                                    value=default.matrix_canvas_res or "1152:896",
                                    info="Resolution of the canvas for matrix generation",
                                ),
                            )
                    with gr.Row():
                        lora_stop_step = r(
                            "lora_stop_step",
                            gr.Number(
                                value=default.lora_stop_step or 45,
                                label="LoRA Stop Step (0 to disable)",
                                precision=0,
                            )
                        )
                        overlay_ratio = r(
                            "overlay_ratio",
                            gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=default.overlay_ratio or 0.3,
                                step=0.01,
                                label="Overlay Ratio",
                            )
                        )

            with gr.Row():
                with gr.Row(scale=7):
                    update_blacklist = gr.Button(
                        "Update Prompt setting",
                        variant="secondary",
                        scale=4,
                    )
                    skip_img = gr.Button("Skip Image", variant="secondary", scale=6)
                skipped_img = gr.Checkbox(
                    value=False,
                    label="Skipped",
                    interactive=False,
                )
                update_blacklist.click(
                    fn=instance.update_prompt_settings,
                    inputs=[
                        lora, header, footer,
                        max_tags, base_chance, add_lora_name,
                        lora_weight, booru_blacklist, booru_pattern_blacklist, prompt_weight_chance, prompt_weight_min, prompt_weight_max, remove_character,
                        enable_random_lora, rnd_lora_select_count
                    ],
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
                        progress = gr.Textbox(
                            label="Generation Progress",
                            placeholder="N/A",
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
                            scale=2,
                            interactive=False,
                        )
                        image = gr.Image(
                            label="Generated Image", type="pil", scale=3, interactive=False
                        )

            var = [
                lora,
                enable_random_lora,
                rnd_lora_select_count,
                header,
                footer,
                max_tags,
                base_chance,
                add_lora_name,
                lora_weight,
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
                preset,
                negative,
                enable_stop,
                stop_mode,
                stop_after_minutes,
                stop_after_images,
                stop_after_datetime,
                enable_neveroom_unet,
                enable_neveroom_vae,
                output_dir,
                output_format,
                output_name,
                save_metadata,
                save_infotext,
                booru_filter_enable,
                booru_model,
                booru_threshold,
                booru_character_threshold,
                booru_allow_rating,
                booru_ignore_questionable,
                booru_save_each_rate,
                booru_merge_sensitive,
                general_save_dir,
                sensitive_save_dir,
                questionable_save_dir,
                explicit_save_dir,
                booru_blacklist,
                booru_pattern_blacklist,
                booru_separate_save,
                booru_blacklist_save_dir,
                active_rp,
                rp_mode,
                rp_calc,
                rp_base,
                rp_base_ratio,
                lora_base,
                add_lora_name_base,
                lora_weight_base,
                header_base,
                footer_base,
                max_tags_base,
                base_chance_base,
                disallow_duplicate_base,
                matrix_split,
                matrix_divide,
                matrix_canvas_res_auto,
                matrix_canvas_res,
                lora_stop_step,
                overlay_ratio,
                prompt_weight_chance,
                prompt_weight_min,
                prompt_weight_max,
                enable_sag,
                sag_strength,
                remove_character,
                save_tmp_images,
                prompt_generation_max_tries,
            ]
            save_all_param = gr.Button("Save current parameters", variant="secondary")

            generate.click(
                fn=instance.start,
                inputs=var,
                outputs=[eta, progress, progress_bar_html, image, output, skipped_img],
            )
            stop.click(fn=instance.stop_generation, inputs=[], outputs=[])

            save_all_param.click(
                fn=forever_generation_from_lora.insta_save,
                inputs=forever_generation_from_lora.values(),
                outputs=[],
            )
            
            enable_random_lora.change(
                fn=lambda lora,enable: gr.Slider.update(interactive=enable, maximum=len(lora)),
                inputs=[lora, enable_random_lora],
                outputs=[rnd_lora_select_count],
            )
            lora.change(
                fn=lambda lora,enable: gr.Slider.update(interactive=enable, maximum=len(lora)),
                inputs=[lora, enable_random_lora],
                outputs=[rnd_lora_select_count],
            )
