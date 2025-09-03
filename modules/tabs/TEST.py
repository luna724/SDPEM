import os
import gradio as gr

from modules.utils.ui.elements import HiddenValue

from webui import UiTabs

class Define(UiTabs):
    def title(self) -> str:
        return "Test"

    def index(self) -> int:
        return 999999
    
    def ui(self, outlet):
        def run(*a):  print(a)
        item = {
            "a": 1,
            "b": 2,
            "c": "3"
        }
        value = HiddenValue(
            os.listdir
        )
        
        btn = gr.Button("Test")
        btn.click(
            fn=run, inputs=[value]
        )
        