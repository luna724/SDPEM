import gradio as gr
import os

from webui import UiTabs

class Database(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "database_child")

    def title(self):
        return "Database-Viewer"

    def index(self):
        return 9999

    def ui(self, outlet):
        with gr.Blocks():
            with gr.Tabs():
                tabs = self.get_ui()
                for tab in tabs:
                    with gr.Tab(tab.title()):
                        tab()