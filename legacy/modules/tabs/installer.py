import gradio as gr
import os

from webui import UiTabs

class Installer(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "installer_child")

    def title(self):
        return "Model-Installer"

    def index(self):
        return 999
