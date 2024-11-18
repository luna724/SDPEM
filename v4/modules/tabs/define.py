import gradio as gr
import os

from v4.webui import UiTabs

class Generate(UiTabs):
  def __init__(self, path):
    super().__init__(path)
    
    self.child_path = os.path.join(UiTabs.PATH, "define_child")

  def title(self):
    return "Define"
  
  def index(self):
    return 1
  
  def ui(self, outlet):
    with gr.Blocks():
      with gr.Tabs():
        tabs = self.get_ui()
        for tab in tabs:
          with gr.Tab(tab.title()):
            tab()
            