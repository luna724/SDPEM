from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import re
from modules.prompt_setting import setting

class FilterPrompt(UiTabs):
    def title(self) -> str:
        return "Prompt Filter"
    def index(self) -> int:
        return 0
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def filter_prompt(prompt: str) -> str:
            p = []
            filtered = 0
            blacklist = setting.obtain_blacklist()
            for tag in prompt.split(","):
                if not any(b.search(tag) for b in blacklist):
                    p.append(tag)
                else:
                    filtered += 1
            return f"Filtered {filtered} tags", ", ".join(p)

        with gr.Column():
            in_prompt = gr.Textbox(
                label="Input Prompt",
                placeholder="Enter your prompt here",
                lines=5,
                max_lines=400,
            )
        
            out_prompt = gr.Textbox(
                label="Output Prompt",
                placeholder="The filtered prompt will appear here",
                lines=5,
                max_lines=400,
                interactive=False, show_copy_button=True
            )
        
        run = gr.Button("Run", variant="primary")
        out = gr.Textbox(
            label="Log", lines=1, interactive=False, show_copy_button=False
        )
        
        run.click(
            fn=filter_prompt,
            inputs=in_prompt,
            outputs=[out, out_prompt]
        )