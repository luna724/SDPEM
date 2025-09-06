import os
import gradio as gr

from modules.utils.ui.elements import AnyComponentValue
from modules.utils.ui.globals import get_components
from modules.utils.ui.register import RegisterComponent

from webui import UiTabs

class Define(UiTabs):
    def title(self) -> str:
        return "Test"

    def index(self) -> int:
        return 999999
    
    def ui(self, outlet):
        # Access the RegisterComponent stored under
        # GlobalReference.forever_generations.from_lora.components
        rc = get_components("forever_generations/from_lora")

        with gr.Blocks():
            header_value = gr.Textbox(
                label="Header value (from from_lora)",
                interactive=False,
            )

            def show_header(v):
                print("[TEST] header:", v)
                return v

            if isinstance(rc, RegisterComponent):
                # Get the actual Gradio component for "header"
                header_comp = rc.components.get("header")
                btn = gr.Button("Show from_lora.header")
                if header_comp is not None:
                    btn.click(fn=show_header, inputs=[header_comp], outputs=[header_value])
                else:
                    gr.Markdown("`header` component not found in from_lora")
            else:
                gr.Markdown("GlobalReference for `forever_generations/from_lora` not available yet")
