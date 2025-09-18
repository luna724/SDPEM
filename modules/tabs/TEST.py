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
        with gr.Row():
            inp = gr.Textbox(label="Input")
            out = gr.Textbox(label="Output")
            
        async def test(
            inp: str
        ) -> str:
            from modules.prompt_placeholder import placeholder
            return await placeholder.process_prompt(
                inp
            )
        
        inp.change(
            fn=test,
            inputs=[inp],
            outputs=[out]
        )