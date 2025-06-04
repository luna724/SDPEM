from webui import UiTabs
import gradio as gr
import os
import shared
from utils import *

class LoRAToPrompt(UiTabs):
  def title(self):
    return "from LoRA"
  def index(self):
    return 1
  def ui(self, outlet):
    async def generate_prompt(
      lora_names, blacklist, pattern_blacklist,
      blacklist_multiplier, use_relative_freq,
      weight_multiplier, w_min, w_max,
      disallow_duplicate, header, footer,
      max_tags, base_chance, add_lora_name, lora_weight
    ):
      prm = {
        "lora_name": lora_names,
        "blacklist": blacklist.split(",") if blacklist else [],
        "black_patterns": pattern_blacklist.splitlines() if pattern_blacklist else [],
        "blacklisted_weight": blacklist_multiplier,
        "use_relative_freq": use_relative_freq,
        "weight_multiplier": weight_multiplier,
        "weight_multiplier_target": [
          w_min,
          w_max
        ],
        "disallow_duplicate": disallow_duplicate,
        "header": header,
        "footer": footer,
        "max_tags": max_tags,
        "base_chance": base_chance,
        "lora_weight": lora_weight,
        "add_lora_name": add_lora_name
      }
      resp = await shared.session.post(
        f"{shared.pem_api}/v1/generator/lora/lora2prompt",
        json=prm
      )
      if resp.status_code != 200 and resp.status_code != 422:
        printwarn("Failed to generate prompt:", resp.status_code, resp.text)
        raise gr.Error(f"Failed to call API ({resp.status_code})")
      result = resp.json()[0]
      if resp.status_code == 422 or result.get("success", True) is False:
        printwarn("API Error:", result.get("message", "Unknown error"))
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
        blacklist = gr.Textbox(
          label="Blacklist tags",
          placeholder="Enter tags to blacklist, separated by commas",
          lines=5, max_lines=400, value="", scale=6
        )
        pattern_blacklist = gr.Textbox(
          label="Blacklist patterns",
          placeholder="Enter regex patterns to blacklist, separated by lines",
          lines=5, max_lines=400, value="", scale=4,
          info="Use regex patterns to blacklist tags. Example: ^tag$ will match exactly 'tag'."
        )
      with gr.Row():
        blacklist_multiplier = gr.Slider(
          0, 5, step=0.01, value=0, label="Blacklisted tags weight multiplier",
        )
        use_relative_freq = gr.Checkbox(
          value=False, label="[Experimental]: Use relative tag frequency",
          info="Use relative tag frequency instead of absolute frequency"
        )
      with gr.Row():
        w_min = gr.Number(
          label="Multiplier target weight minimum",
          value=1, precision=0, step=1, min=0, max=10000, scale=3
        )
        w_max = gr.Number(
          label="Multiplier target weight maximum",
          value=12, precision=0, step=1, min=0, max=10000, scale=3
        )
        w_multiplier = gr.Slider(
          0, 10, step=0.01, value=2, label="Weight multiplier",
          info="Multiplier for the tag weight", scale=4
        )
      with gr.Row():
        add_lora_name = gr.Checkbox(
          value=True, label="Add LoRA name to prompt",
          info="If enabled, the LoRA name will be added to the prompt", scale=2
        )
        lora_weight = gr.Slider(
          0, 1, step=0.01, value=0.5, label="LoRA weight",
          info="Weight of the LoRA in the prompt", scale=4
        )
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
        max_tags = gr.Number(
          label="Max tags",
          value=7, precision=0, step=1, min=1, max=100, scale=3
        )
        base_chance = gr.Slider(
          0.01, 10, step=0.01, value=10, label="Base chance",
          info="Base chance for the tag to be included in the prompt", scale=4
        )
        disallow_duplicate = gr.Checkbox(
          value=True, label="Disallow duplicate tags",
          info="If enabled, duplicate tags will not be included in the prompt"
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
          lora, blacklist, pattern_blacklist,
          blacklist_multiplier, use_relative_freq,
          w_multiplier, w_min, w_max,
          disallow_duplicate, header, footer,
          max_tags, base_chance, add_lora_name, lora_weight
        ],
        outputs=output
      )