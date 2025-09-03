from webui import UiTabs
from modules.utils.ui.register import RegisterComponent
from pathlib import Path

import gradio as gr


class FromLoRARegionalPrompter(UiTabs):
    def title(self):
        return "From LoRA (RP)"

    def index(self):
        return 2

    def ui(self, outlet):
        forever_generation_from_lora_rp = RegisterComponent(
            Path("./defaults/forever_generation.from_lora_rp.json"),
            "forever_generations/from_lora_rp",
        )
        r = forever_generation_from_lora_rp.register
        default = forever_generation_from_lora_rp.get()

        with gr.Blocks():
            with gr.Row():
                with gr.Column():
                    with gr.Accordion(
                        label="Prompt Settings (A)",
                        open=False,
                    ):
                        with gr.Row():
                            blacklist_a = r(
                                "blacklist_a",
                                gr.Textbox(
                                    label="Blacklist tags",
                                    placeholder="Enter tags to blacklist, separated by commas",
                                    lines=5,
                                    max_lines=400,
                                    value=default.blacklist,
                                    scale=6,
                                ),
                            )
                            pattern_blacklist_a = r(
                                "pattern_blacklist_a",
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
                            blacklist_multiplier_a = r(
                                "blacklist_multiplier_a",
                                gr.Slider(
                                    0,
                                    5,
                                    step=0.01,
                                    value=default.blacklist_multiplier,
                                    label="Blacklisted tags weight multiplier",
                                ),
                            )
                            use_relative_freq_a = r(
                                "use_relative_freq_a",
                                gr.Checkbox(
                                    value=default.use_relative_freq,
                                    label="[Experimental]: Use relative tag frequency",
                                    info="Use relative tag frequency instead of absolute frequency",
                                ),
                            )
                        with gr.Row():
                            w_min_a = r(
                                "w_min_a",
                                gr.Number(
                                    label="Multiplier target weight minimum",
                                    value=default.w_min,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            w_max_a = r(
                                "w_max_a",
                                gr.Number(
                                    label="Multiplier target weight maximum",
                                    value=default.w_max,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            w_multiplier_a = r(
                                "w_multiplier_a",
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
                            add_lora_name_a = r(
                                "add_lora_name_a",
                                gr.Checkbox(
                                    value=default.add_lora_name,
                                    label="Add LoRA name to prompt",
                                    info="If enabled, the LoRA name will be added to the prompt",
                                    scale=2,
                                ),
                            )
                            lora_weight_a = r(
                                "lora_weight_a",
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
                        header_a = r(
                            "header_a",
                            gr.Textbox(
                                label="Prompt Header",
                                placeholder="Enter the prompt header",
                                lines=2,
                                max_lines=5,
                                value=default.header,
                            ),
                        )
                        footer_a = r(
                            "footer_a",
                            gr.Textbox(
                                label="Prompt Footer",
                                placeholder="Enter the prompt footer",
                                lines=2,
                                max_lines=5,
                                value=default.footer,
                            ),
                        )
                        with gr.Row():
                            max_tags_a = r(
                                "max_tags_a",
                                gr.Number(
                                    label="Max tags",
                                    value=default.max_tags,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            base_chance_a = r(
                                "base_chance_a",
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
                            disallow_duplicate_a = r(
                                "disallow_duplicate_a",
                                gr.Checkbox(
                                    value=default.disallow_duplicate,
                                    label="Disallow duplicate tags",
                                    info="If enabled, duplicate tags will not be included in the prompt",
                                ),
                            )

                with gr.Column():
                    with gr.Accordion(
                        label="Prompt Settings (B)",
                        open=False,
                    ):
                        with gr.Row():
                            blacklist_b = r(
                                "blacklist_b",
                                gr.Textbox(
                                    label="Blacklist tags",
                                    placeholder="Enter tags to blacklist, separated by commas",
                                    lines=5,
                                    max_lines=400,
                                    value=default.blacklist,
                                    scale=6,
                                ),
                            )
                            pattern_blacklist_b = r(
                                "pattern_blacklist_b",
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
                            blacklist_multiplier_b = r(
                                "blacklist_multiplier_b",
                                gr.Slider(
                                    0,
                                    5,
                                    step=0.01,
                                    value=default.blacklist_multiplier,
                                    label="Blacklisted tags weight multiplier",
                                ),
                            )
                            use_relative_freq_b = r(
                                "use_relative_freq_b",
                                gr.Checkbox(
                                    value=default.use_relative_freq,
                                    label="[Experimental]: Use relative tag frequency",
                                    info="Use relative tag frequency instead of absolute frequency",
                                ),
                            )
                        with gr.Row():
                            w_min_b = r(
                                "w_min_b",
                                gr.Number(
                                    label="Multiplier target weight minimum",
                                    value=default.w_min,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            w_max_b = r(
                                "w_max_b",
                                gr.Number(
                                    label="Multiplier target weight maximum",
                                    value=default.w_max,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            w_multiplier_b = r(
                                "w_multiplier_b",
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
                            add_lora_name_b = r(
                                "add_lora_name_b",
                                gr.Checkbox(
                                    value=default.add_lora_name,
                                    label="Add LoRA name to prompt",
                                    info="If enabled, the LoRA name will be added to the prompt",
                                    scale=2,
                                ),
                            )
                            lora_weight_b = r(
                                "lora_weight_b",
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
                        header_b = r(
                            "header_b",
                            gr.Textbox(
                                label="Prompt Header",
                                placeholder="Enter the prompt header",
                                lines=2,
                                max_lines=5,
                                value=default.header,
                            ),
                        )
                        footer_b = r(
                            "footer_b",
                            gr.Textbox(
                                label="Prompt Footer",
                                placeholder="Enter the prompt footer",
                                lines=2,
                                max_lines=5,
                                value=default.footer,
                            ),
                        )
                        with gr.Row():
                            max_tags_b = r(
                                "max_tags_b",
                                gr.Number(
                                    label="Max tags",
                                    value=default.max_tags,
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            base_chance_b = r(
                                "base_chance_b",
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
                            disallow_duplicate_b = r(
                                "disallow_duplicate_b",
                                gr.Checkbox(
                                    value=default.disallow_duplicate,
                                    label="Disallow duplicate tags",
                                    info="If enabled, duplicate tags will not be included in the prompt",
                                ),
                            )
