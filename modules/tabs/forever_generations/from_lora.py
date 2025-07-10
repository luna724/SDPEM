from modules.forever.from_lora import ForeverGenerationFromLoRA
from modules.utils.browse import select_folder
from modules.utils.register_ui import RegisterComponent
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
            lora = r(
                "lora",
                gr.Dropdown(
                    choices=[
                        x
                        for x in os.listdir(
                            os.path.join(shared.api_path, "models/Lora")
                        )
                        if x.endswith(".safetensors")
                    ],
                    multiselect=True,
                    value=default.lora,
                    label="Target LoRA",
                ),
            )
            with gr.Row():
                with gr.Accordion(label="Prompt Settings", open=False):
                    with gr.Row():
                        blacklist = r(
                            "blacklist",
                            gr.Textbox(
                                label="Blacklist tags",
                                placeholder="Enter tags to blacklist, separated by commas",
                                lines=5,
                                max_lines=400,
                                value=default.blacklist,
                                scale=6,
                            ),
                        )
                        pattern_blacklist = r(
                            "pattern_blacklist",
                            gr.Textbox(
                                label="Blacklist patterns",
                                placeholder="Enter regex patterns to blacklist, separated by lines",
                                lines=5,
                                max_lines=400,
                                value=default.pattern_blacklist,
                                scale=4,
                                info="Use regex patterns to blacklist tags. Example: ^tag$ will match exactly 'tag'.",
                            ),
                        )
                    with gr.Row():
                        blacklist_multiplier = r(
                            "blacklist_multiplier",
                            gr.Slider(
                                0,
                                5,
                                step=0.01,
                                value=default.blacklist_multiplier,
                                label="Blacklisted tags weight multiplier",
                            ),
                        )
                        use_relative_freq = r(
                            "use_relative_freq",
                            gr.Checkbox(
                                value=default.use_relative_freq,
                                label="[Experimental]: Use relative tag frequency",
                                info="Use relative tag frequency instead of absolute frequency",
                            ),
                        )
                    with gr.Row():
                        w_min = r(
                            "w_min",
                            gr.Number(
                                label="Multiplier target weight minimum",
                                value=default.w_min,
                                precision=0,
                                scale=3,
                            ),
                        )
                        w_max = r(
                            "w_max",
                            gr.Number(
                                label="Multiplier target weight maximum",
                                value=default.w_max,
                                precision=0,
                                scale=3,
                            ),
                        )
                        w_multiplier = r(
                            "w_multiplier",
                            gr.Slider(
                                0,
                                10,
                                step=0.01,
                                value=default.w_multiplier,
                                label="Weight multiplier",
                                info="Multiplier for the tag weight",
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
                            gr.Slider(
                                0,
                                1,
                                step=0.01,
                                value=default.lora_weight,
                                label="LoRA weight",
                                info="Weight of the LoRA in the prompt",
                                scale=4,
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
                        disallow_duplicate = r(
                            "disallow_duplicate",
                            gr.Checkbox(
                                value=default.disallow_duplicate,
                                label="Disallow duplicate tags",
                                info="If enabled, duplicate tags will not be included in the prompt",
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
                        with gr.Column():
                            batch_count = r(
                                "batch_count",
                                gr.Number(
                                    label="Batch Count",
                                    value=default.batch_count,
                                    precision=0
                                ),
                            )
                            batch_size = r(
                                "batch_size",
                                gr.Number(
                                    label="Batch Size",
                                    value=default.batch_size,
                                    precision=0
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
                    with gr.Row():
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
                    pass  # TODO: implement

            with gr.Row():
                skip_img = gr.Button("Skip Image", variant="secondary", scale=7)
                skipped_img = gr.Checkbox(
                    value=False,
                    label="Skipped",
                    interactive=False,
                )
                skip_img.click(fn=instance.skip_image, inputs=[], outputs=[skipped_img])

            generate = gr.Button("Start", variant="primary")
            stop = gr.Button(
                "Stop",
                variant="primary",
            )
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
                        label="Progress",
                        placeholder="Generation progress",
                        lines=1,
                        max_lines=1,
                        value="",
                        scale=2,
                        interactive=False,
                    )
                    output = gr.Textbox(
                        label="test",
                        placeholder="",
                        lines=5,
                        max_lines=10,
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
                blacklist,
                pattern_blacklist,
                blacklist_multiplier,
                use_relative_freq,
                w_multiplier,
                w_min,
                w_max,
                disallow_duplicate,
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
            ]
            save_all_param = gr.Button("Save current parameters", variant="secondary")

            # パラメータ保存機能
            def save_all_parameters(*args):
                """すべてのパラメータをJSONに保存"""
                gr.Info("Saving..")
                return forever_generation_from_lora.save(args)

            generate.click(
                fn=instance.start,
                inputs=var,
                outputs=[eta, progress, progress_bar_html, image, output],
            )
            stop.click(fn=instance.stop_generation, inputs=[], outputs=[])

            save_all_param.click(fn=save_all_parameters, inputs=forever_generation_from_lora.values(), outputs=[output])
