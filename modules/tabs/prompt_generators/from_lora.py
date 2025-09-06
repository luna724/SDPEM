from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

from modules.prompt_setting import setting

class LoRAToPrompt(UiTabs):
  def title(self) -> str:
    return "from LoRA"
  def index(self) -> int:
    return 1
  def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
    async def generate_prompt(
      lora_names, header, footer,
      tag_count, base_chance, add_lora_name, lora_weight,
      add_prompt_weight, prompt_weight_min, prompt_weight_max
    ) -> str:
      prm = {
        "lora_name": lora_names,
        "header": header,
        "footer": footer,
        "tag_count": tag_count,
        "base_chance": base_chance,
        "lora_weight": lora_weight,
        "add_lora_name": add_lora_name,
        "prompt_weight_chance": add_prompt_weight,
        "prompt_weight_range": (prompt_weight_min, prompt_weight_max)
      } | setting.request_param()
      resp = await shared.session.post(
        f"{shared.pem_api}/v1_1/generator/lora/lora2prompt",
        json=prm
      )
      if resp.status_code != 200 and resp.status_code != 422:
        error("Failed to generate prompt:", resp.status_code, resp.text)
        raise gr.Error(f"Failed to call API ({resp.status_code})")
      result = resp.json()
      if resp.status_code == 422 or result.get("success", True) is False:
        warn("API Error:", result.get("message", "Unknown error"))
        return "[API Error]: " + result["message"]

      return result.get("prompt", "")

    with gr.Blocks():
      lora = gr.Dropdown(
        choices=[
          x for x in os.listdir(os.path.join(shared.api_path, "models/Lora"))
          if x.endswith(".safetensors")
        ],
        multiselect=True, value=[],
        label="Target LoRA"
      )
      with gr.Row():
        add_lora_name = gr.Checkbox(
          value=True, label="Add LoRA name to prompt",
          info="If enabled, the LoRA name will be added to the prompt", scale=2
        )
        lora_weight = gr.Textbox(
          label="LoRA weight",
          placeholder="lbw=OUTALL:stop=20",
          value="0.5", lines=1, max_lines=1, scale=2
        )
      with gr.Row():
        header = gr.Textbox(
          label="Prompt Header",
          placeholder="Enter the prompt header",
          lines=2, max_lines=5, value=""
        )
        footer = gr.Textbox(
          label="Prompt Footer",
          placeholder="Enter the prompt footer",
          lines=2, max_lines=5, value=""
        )
      with gr.Row():
        tag_count = gr.Number(
          label="tag count",
          value=7, scale=3
        )
        base_chance = gr.Slider(
          0.01, 10, step=0.01, value=10, label="Base chance",
          info="Base chance for the tag to be included in the prompt", scale=4
        )
      with gr.Row():
        add_prompt_weight = gr.Slider(
          0, 1, label="Add prompt weight change",
          info="0 to disable", value=0.05, step=0.01
        )
        with gr.Column():
          prompt_weight_min = gr.Slider(
            0, 2, step=0.01, value=0.5, label="Prompt weight min",
            info="Minimum prompt weight",
          )
          prompt_weight_max = gr.Slider(
            0, 2, step=0.01, value=1.5, label="Prompt weight max",
            info="Maximum prompt weight",
          )
        
      generate = gr.Button("Generate Prompt", variant="primary")
      output = gr.Textbox(
        label="Generated Prompt",
        placeholder="The generated prompt will be displayed here",
        lines=5, max_lines=10, value=""
      )
      generate.click(
        fn=generate_prompt,
        inputs=[
          lora, header, footer,
          tag_count, base_chance, add_lora_name, lora_weight,
          add_prompt_weight, prompt_weight_min, prompt_weight_max
        ],
        outputs=output
      )