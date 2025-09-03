import os

from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "settings")

    def title(self) -> str:
        return "Settings"

    def index(self) -> int:
        return 99999