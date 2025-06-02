from webui import UiTabs

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "share_util_child")

    def title(self):
        return "Share-Util"

    def index(self):
        return 88888