from modules.utils.lora_util import list_lora_with_tags
from webui import UiTabs
from modules.utils.ui.register import RegisterComponent
from pathlib import Path

import gradio as gr


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
            with gr.Row():
                def create_prompt_setting(discriminator):
                    d = discriminator.lower()
                    with gr.Accordion(label="Prompt Settings", open=False):
                        with gr.Row():
                            max_tags = r(
                                f"max_tags"+d,
                                gr.Number(
                                    label="Max tags",
                                    value=getattr(default, "max_tags"+d),
                                    precision=0,
                                    scale=3,
                                ),
                            )
                            base_chance = r(
                                "base_chance"+d,
                                gr.Slider(
                                    0.01,
                                    10,
                                    step=0.01,
                                    value=getattr(default, "base_chance"+d),
                                    label="Base chance",
                                    info="Base chance for the tag to be included in the prompt",
                                    scale=4,
                                ),
                            )
                        with gr.Row():
                            add_lora_name = r(
                                "add_lora_name"+d,
                                gr.Checkbox(
                                    value=getattr(default, "add_lora_name"+d),
                                    label="Add LoRA name to prompt",
                                    info="If enabled, the LoRA name will be added to the prompt",
                                    scale=2,
                                ),
                            )
                            lora_weight = r(
                                "lora_weight"+d,
                                gr.Textbox(
                                label="LoRA weight",
                                placeholder="lbw=OUTALL:stop=20",
                                value=str(getattr(default, "lora_weight"+d)) if getattr(default, "lora_weight"+d) else "0.5", lines=1, max_lines=1, scale=2
                                ),
                            )
                        header = r(
                            "header"+d,
                            gr.Textbox(
                                label="Prompt Header",
                                placeholder="Enter the prompt header",
                                lines=2,
                                max_lines=5,
                                value=getattr(default, "header"+d),
                            ),
                        )
                        footer = r(
                            "footer"+d,
                            gr.Textbox(
                                label="Prompt Footer",
                                placeholder="Enter the prompt footer",
                                lines=2,
                                max_lines=5,
                                value=getattr(default, "footer"+d),
                            ),
                        )
                        with gr.Row():
                            prompt_weight_chance = r(
                                "prompt_weight_chance"+d,
                                gr.Slider(
                                    0, 1, label="Add prompt weight change",
                                    info="0 to disable", value=default.prompt_weight_chance+d, step=0.01
                                ),
                            )
                            with gr.Column():
                                prompt_weight_min = r(
                                    "prompt_weight_min"+d,
                                    gr.Slider(
                                    0, 2, step=0.01, value=default.prompt_weight_min+d, label="Prompt weight min",
                                    info="Minimum prompt weight",
                                    ),
                                )
                                prompt_weight_max = r(
                                    "prompt_weight_max"+d,
                                    gr.Slider(
                                        0, 2, step=0.01, value=default.prompt_weight_max+d, label="Prompt weight max",
                                        info="Maximum prompt weight",
                                    )
                                )
                        with gr.Row():
                            remove_character = r(
                                "remove_character"+d,
                                gr.Checkbox(
                                    value=getattr(default, "remove_character"+d), label="Remove additional character tags",
                                ),
                            )
                    return []
                
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