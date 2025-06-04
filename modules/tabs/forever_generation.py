import os

from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "forever_generations")

    def title(self):
        return "Forever Image Generation"

    def index(self):
        return 0