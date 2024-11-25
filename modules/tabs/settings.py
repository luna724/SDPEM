import gradio as gr
import os

from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "settings_child")

    def title(self):
        return "Settings"

    def index(self):
        return 99999