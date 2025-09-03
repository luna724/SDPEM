from webui import UiTabs
import gradio as gr
from typing import Callable
from utils import *
from pathlib import Path
from modules.utils.ui.register import RegisterComponent
from modules.prompt_setting import setting

class Prompt(UiTabs):
    def title(self) -> str:
        return "Prompt"
    def index(self) -> int:
        return 0

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]):
        prompt_settings = RegisterComponent(
            Path("./defaults/prompt_settings.json"),
            "settings/prompt_settings",
        )
        self.register_comp_instance = prompt_settings
        r = prompt_settings.register
        default = prompt_settings.get()
        
        with gr.Blocks():
            with gr.Accordion("Blacklists", open=True):
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
                            max_lines=800,
                            value=default.pattern_blacklist,
                            scale=4,
                            info="Use regex patterns to blacklist tags. Example: ^tag$ will match exactly 'tag'.",
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
            
            with gr.Accordion("From FrequencyLike", open=True):
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
                
        async def push(*args):
            prompt_settings.save(args)
            gr.Info("Saved")
            return await setting.push_ui(*args)
            
        apply = gr.Button("Apply", variant="primary", )
        apply.click(
            fn=push,
            inputs=prompt_settings.values(),
        )