import gradio as gr
import os

from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Define"

    def index(self):
        return 9

    def ui(self, outlet):
        with gr.Blocks():
            with gr.Tabs():
                tabs = self.get_ui()
                for tab in tabs:
                    with gr.Tab(tab.title()):
                        tab()