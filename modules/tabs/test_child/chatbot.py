from webui import UiTabs

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Chatbot"

    def index(self):
        return 6

    def ui(self, outlet):
        with gr.Blocks():
            prompt = gr.Textbox(
                label="Prompt"
            )
            with gr.Row():
                length = gr.Slider(
                    label="Max Length",
                    minimum=1, maximum=25565, step=1,
                    value=100
                )
                temperature = gr.Slider(
                    label="Temperature",
                    minimum=0, maximum=1, step=0.01,
                    value=0.7
                )
            with gr.Row():
                top_p = gr.Slider(
                    label="Top P",
                    minimum=0, maximum=1, step=0.01,
                    value=0.9
                )
                top_k = gr.Slider(
                    label="Top K",
                    minimum=1, maximum=100, step=1,
                    value=40
                )

            output = gr.Textbox(
                label="Output"
            )
            run = gr.Button("Run", variant="primary")

            def simple_talk(p, l, t, k, tp):
                from modules.models import ollama
                return ollama.default.infer(p, l, t, k, tp)

            run.click(
                simple_talk,
                inputs=[prompt, length, temperature, top_k, top_p],
                outputs=output
            )