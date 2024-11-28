import gradio as gr
import os

from modules.character_template import CharacterTemplate
from modules.simple_template import SimpleTemplate
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Simple-Template"

    def index(self):
        return 0

    def ui(self, outlet):
        module = CharacterTemplate()
