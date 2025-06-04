import os

from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "prompt_generators")

    def title(self):
        return "Prompt Generator"

    def index(self):
        return 1