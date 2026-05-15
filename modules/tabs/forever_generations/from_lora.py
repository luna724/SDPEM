from modules.forever.from_lora import ForeverGenerationFromLoRA
from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent
from modules.utils.lora_util import list_lora_with_tags
from modules.preset import PresetManager
from modules.sd_param import get_sampler, get_scheduler
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
            "forever_generation/from_lora",
        )
        r = forever_generation_from_lora
        pmgr = forever_generation_from_lora.pmgr
        default = forever_generation_from_lora.get()

        with gr.Blocks():
            with gr.Group():
                with gr.Row():
                    lora = r(
                        "lora",
                        gr.Dropdown(
                            choices=list_lora_with_tags(),
                            multiselect=True,
                            value=default.lora,
                            label="Target LoRA",
                            scale=19,
                        ),
                    )
                    lora_add_all_btn = gr.Button("*", variant="secondary", scale=1)
                    lora_add_all_btn.click(
                        fn=lambda: list_lora_with_tags(),
                        outputs=[lora],
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
                    )
                )
            
            with gr.Row():
                lora_weight = r(
                    "lora_weight",
                    gr.Textbox(
                    label="LoRA weight",
                    placeholder="lbw=OUTALL:stop=20",
                    value=str(default.lora_weight) if default.lora_weight else "0.5", lines=1, max_lines=1, scale=2
                    ),
                )
                lora_weight_prio = r(
                    "lora_weight_prio",
                    gr.Radio(
                        choices=["lorainfo", "setting"],
                        value=default.lora_weight_prio,
                        label="LoRA weight src priority",
                    )
                )

            enable_random_lora.change(
                fn=lambda lora,enable: gr.Slider(interactive=enable, maximum=len(lora)),
                inputs=[lora, enable_random_lora],
                outputs=[rnd_lora_select_count],
                show_progress=False
            )
            
            def on_lora_change_a(lora, enable):
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

            lora.change(
                fn=on_lora_change_a,
                inputs=[lora, enable_random_lora],
                outputs=[enable_random_lora, rnd_lora_select_count],
                show_progress=False
            )
