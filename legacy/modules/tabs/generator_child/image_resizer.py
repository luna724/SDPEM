import gradio as gr
import os

from webui import UiTabs

class Generator(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "generator_child/image_resizer_child")

    def title(self):
        return "Image-Resizer"

    def index(self):
        return 99