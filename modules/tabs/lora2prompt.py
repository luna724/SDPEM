from webui import UiTabs
import gradio as gr
import aiohttp

class LoRAToPrompt(UiTabs):
  def title(self):
    return "LoRA2Prompt"
  def index(self):
    return 1
  def ui(self, outlet: callable):
    with gr.Blocks():
      