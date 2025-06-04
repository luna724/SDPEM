from modules.forever.from_lora import ForeverGenerationFromLoRA
from webui import UiTabs
import gradio as gr
import os
import shared
import requests
from utils import *

class LoRAToPrompt(UiTabs):
  def title(self):
    return "from LoRA"
  def index(self):
    return 1
  def ui(self, outlet):
    instance = ForeverGenerationFromLoRA()
    def get_opts(mode: str):
      resp = requests.get(f"{shared.pem_api}/v1/items/sdapi/{mode}")
      
      if resp.status_code != 200:
        printwarn("Failed to get options:", resp.status_code, resp.content.decode())
        raise gr.Error(f"Failed to call API ({resp.status_code})")
      return list(resp.json()[0])
      
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
        with gr.Accordion(label="Prompt Settings", open=False):
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

        with gr.Accordion(label="Parameter Settings", open=False):
          with gr.Row():
            s_method = gr.Dropdown(
              choices=get_opts("samplers"),
              label="Sampling Methods", value=["DPM++ 2M SDE", "Euler a"],
              multiselect=True, scale=6
            )
            scheduler = gr.Dropdown(
              choices=get_opts("schedulers"),
              label="Scheduler", value=["Automatic"],
              multiselect=True, scale=4
            )
          with gr.Row():
            with gr.Column():
              steps_min = gr.Slider(
                1, 150, step=1, value=20,
                label="Min Sampling Steps"
              )
              steps_max = gr.Slider(
                1, 150, step=1, value=70,
                label="Max Sampling Steps"
              )
            with gr.Column():
              cfg_min = gr.Slider(
                0.1, 30, step=0.1, value=5,
                label="Min CFG Scale"
              )
              cfg_max = gr.Slider(
                0.1, 30, step=0.1, value=9,
                label="Max CFG Scale"
              )
            with gr.Column():
              batch_count = gr.Number(
                label="Batch Count", value=1, precision=0, step=1, min=1, max=100
              )
              batch_size = gr.Number(
                label="Batch Size", value=2, precision=0, step=1, min=1, max=8
              )
          
          size = gr.Textbox(
            label="Image Size(s) (w:h,w:h,...) (separate by commas)",
            placeholder="e.g. 896:1152,1024:1024,1152:896",
            value="896:1152,1024:1024,1152:896",
          )
          with gr.Accordion(label="ADetailer (Simplified)", open=False):
            adetailer = gr.Checkbox(
              value=False, label="Enable ADetailer with Template",
              info="Enable ADetailer for image generation"
            )
            enable_hand_tap = gr.Checkbox(
              value=True, label="Enable Hand Restoration",
              info="Enable hand_yolov8s.pt detector"
            )
            disable_lora_in_adetailer = gr.Checkbox(
              value=False, label="Disable LoRA Trigger in ADetailer",
              info="If enabled, LoRA trigger (<lora:name:.0>) will not be applied in ADetailer"
            )
          with gr.Accordion(label="FreeU (Integrated for ForgeUI)", open=False):
            enable_freeu = gr.Checkbox(
              value=True, label="Enable FreeU",
              info="Enable FreeU for image generation"
            )
            preset = gr.Dropdown(
              choices=["SDXL", "SD 1.X"],
              label="FreeU Preset", value="SDXL",
            )
          negative = gr.Textbox(
            label="Negative Prompt",
            placeholder="Enter the negative prompt",
            lines=2, max_lines=5, value="score_6, score_5, score_4, ugly face, low res"
          )
      
      generate = gr.Button("Start", variant="primary")
      with gr.Row():
        with gr.Column():
          eta = gr.Textbox(
            label="ETA",
            placeholder="Estimated time of arrival",
            lines=1, max_lines=1, value="", scale=2, interactive=False
          )
          progress = gr.Textbox(
            label="Progress",
            placeholder="Generation progress",
            lines=1, max_lines=1, value="", scale=2, interactive=False
          )
          output = gr.Textbox(
            label="test",
            placeholder="",
            lines=5, max_lines=10, value="", scale=3
          )
        
        with gr.Column():
          progress_bar_html = gr.HTML(
            label="Progress Bar",
            value="<div style='width: 100%; height: 20px; background-color: #f3f3f3; border-radius: 5px;'><div style='width: 0%; height: 100%; background-color: #4caf50; border-radius: 5px;'></div></div>",
            scale=2, interactive=False
          )
          image = gr.Image(label="Generated Image", type="pil", scale=3, interactive=False)
          
      generate.click(
        fn=instance.start,
        inputs=[
          lora, blacklist, pattern_blacklist,
          blacklist_multiplier, use_relative_freq,
          w_multiplier, w_min, w_max,
          disallow_duplicate, header, footer,
          max_tags, base_chance, add_lora_name, lora_weight,
          s_method, scheduler, steps_min, steps_max,
          cfg_min, cfg_max, batch_count, batch_size,
          size, adetailer, enable_hand_tap,
          disable_lora_in_adetailer, enable_freeu, preset, negative
        ],
        outputs=[eta, progress, progress_bar_html, image]
      )