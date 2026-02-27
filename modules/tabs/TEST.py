import os
import gradio as gr

from modules.utils.ui.elements import AnyComponentValue
from modules.utils.ui.globals import get_components
from modules.utils.ui.register import RegisterComponent

from webui import UiTabs

class Define(UiTabs):
    def title(self) -> str:
        return "Test"

    def index(self) -> int:
        return 999999
    
    def ui(self, outlet):
        pass