import os
from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
import json

from webui import UiTabs

class TagJar(UiTabs):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "tag_jar")

    def title(self) -> str:
        return "Tag Jar"

    def index(self) -> int:
        return 9999
      
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
      pass