from modules.prompt_alias import PromptAlias
from webui import UiTabs

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Alias test"

    def index(self):
        return 5

    def ui(self, outlet):
        with gr.Blocks():
            prompt = gr.Textbox(
                label="Prompt"
            )

            output = gr.Textbox(
                label="Output"
            )
            run = gr.Button("Run", variant="primary")

            def run_alias(p):
                cls = PromptAlias()
                return cls.process_command(p)
            run.click(
                run_alias,
                inputs=[prompt],
                outputs=[output]
            )