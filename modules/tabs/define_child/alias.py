import gradio as gr

from modules.prompt_alias import PromptAlias
from webui import UiTabs


class UiPromptAlias(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = UiTabs.PATH

    def title(self):
        return "Prompt Alias"

    def index(self):
        return 1

    def ui(self, outlet):
        cls = PromptAlias()
        with gr.Blocks():
            with gr.Row():
                alias = gr.Textbox(
                    label="Alias", placeholder="Enter alias", lines=1, max_lines=1, scale=3
                )
                prompt = gr.Textbox(
                    label="Prompt", placeholder="Enter prompt", lines=1, max_lines=1, scale=7
                )
            info = gr.Textbox(
                label="Alias info"
            )

            with gr.Row():
                add = gr.Button("Add", variant="primary")
                rem = gr.Button("Remove", variant="secondary")

            with gr.Accordion("Current value", open=False):
                value = gr.Json(label="Current")


            def add_tunnel(*args) -> dict:
                gr.Warning(cls.add(*args))
                return cls.get()

            def rem_tunnel(*args) -> dict:
                gr.Warning(cls.remove(*args))
                return cls.get()

            add.click(
                add_tunnel,
                inputs=[alias, prompt, info],
                outputs=[value]
            )

            rem.click(
                rem_tunnel,
                inputs=[alias],
                outputs=[value]
            )