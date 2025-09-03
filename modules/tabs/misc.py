import os

from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "miscs")

    def title(self) -> str:
        return "Miscellaneous"

    def index(self) -> int:
        return 999