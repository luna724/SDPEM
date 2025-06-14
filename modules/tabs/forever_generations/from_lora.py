from modules.forever.from_lora import ForeverGenerationFromLoRA
from modules.utils.browse import select_folder
from webui import UiTabs
import gradio as gr
import os
import shared
import requests
from typing import Callable, List
from utils import *

class LoRAToPrompt(UiTabs):
  def title(self) -> str:
    return "from LoRA"
  def index(self) -> int:
    return 1
  def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
    instance = ForeverGenerationFromLoRA()
    def get_opts(mode: str) -> List[str]:
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
              value=True, label="Enable ADetailer with Template",
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
      with gr.Row():
        with gr.Accordion(label="Image Filtering", open=False):
          with gr.Row():
            booru_filter_enable = gr.Checkbox(
              value=False, label="Enable Caption Filter",
            )
            booru_model = gr.Dropdown(
              choices=[
                      x["display_name"]
                      for x in shared.models["wd-tagger"]
              ], # TODO: wd以外のtaggerからも取得するように
              value="WD1.4 Vit Tagger v3",
              label="Tagger Model",
            )
          with gr.Row():
            booru_threshold = gr.Slider(
              minimum=0.0, maximum=1.0, value=0.65,
              label="Caption Filter Threshold",
              step=0.01, info="Threshold for the caption filter"
            )
            booru_character_threshold = gr.Slider(
              minimum=0.0, maximum=1.0, value=0.45,
              label="Character Filter Threshold",
              step=0.01, info="Threshold for the character filter"
            )
          with gr.Row():
            booru_allow_rating = gr.Dropdown(
              choices=["general", "sensitive", "questionable", "explicit"],
              value=["general", "sensitive", "questionable", "explicit"],
              multiselect=True,
              label="[wip] Allow Ratings",
              scale=6
            )
            booru_ignore_questionable = gr.Checkbox(
              value=True, label="Ignore Questionable",
              info="If enabled, questionable weight will be ignored (questionable 99%, sensitive 1% will be treated as sensitive 100%)", scale=4
            )
            
          with gr.Accordion(label="Save Option", open=False):
            def set_visible_from_rating(allow_rate):
              g = "general" in allow_rate
              s = "sensitive" in allow_rate
              q = "questionable" in allow_rate
              e = "explicit" in allow_rate
              return (
                gr.update(visible=g),
                gr.update(visible=s),
                gr.update(visible=q),
                gr.update(visible=e),
              )

            with gr.Row():
              booru_save_each_rate = gr.Checkbox(
                value=False, label="Save Each Rating",
              )
              
              booru_merge_sensitive = gr.Checkbox(
                value=True, label="Merge Sensitive to general"
              )
            with gr.Row(visible=True) as general_row:
              general_save_dir = gr.Textbox(
                label="[Rating] General Save Directory",
                placeholder="Enter the general save directory",
                value=os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem/general"),
                lines=1, max_lines=1, scale=19
              )
              general_browse_dir = gr.Button(
                "📁", variant="secondary",
                scale=1
              )
              general_browse_dir.click(
                fn=select_folder,
                outputs=[general_save_dir]
              )
            with gr.Row(visible=True) as sensitive_row:
              sensitive_save_dir = gr.Textbox(
                label="[Rating] Sensitive Save Directory",
                placeholder="Enter the sensitive save directory",
                value=os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem/sensitive"),
                lines=1, max_lines=1, scale=19
              )
              sensitive_browse_dir = gr.Button(
                "📁", variant="secondary",
                scale=1
              )
              sensitive_browse_dir.click(
                fn=select_folder,
                outputs=[sensitive_save_dir]
              )

            with gr.Row(visible=True) as questionable_row:
              questionable_save_dir = gr.Textbox(
                label="[Rating] Questionable Save Directory",
                placeholder="Enter the questionable save directory",
                value=os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem/questionable"),
                lines=1, max_lines=1, scale=19
              )
              questionable_browse_dir = gr.Button(
                "📁", variant="secondary",
                scale=1
              )
              questionable_browse_dir.click(
                fn=select_folder,
                outputs=[questionable_save_dir]
              )
            
            with gr.Row(visible=True) as explicit_row:
              explicit_save_dir = gr.Textbox(
                label="[Rating] Explicit Save Directory",
                placeholder="Enter the explicit save directory",
                value=os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem/explicit"),
                lines=1, max_lines=1, scale=19
              )
              explicit_browse_dir = gr.Button(
                "📁", variant="secondary",
                scale=1
              )
              explicit_browse_dir.click(
                fn=select_folder,
                outputs=[explicit_save_dir]
              )
            
            booru_allow_rating.change(
              fn=set_visible_from_rating,
              inputs=[booru_allow_rating],
              outputs=[
                general_row, sensitive_row, questionable_row, explicit_row
              ]
            )
          with gr.Row():
            booru_blacklist = gr.Textbox(
              label="Caption Blacklist",
              placeholder="Enter caption tags to blacklist, separated by commas",
              info="if this tag is in the caption, the image will be skipped (or saved at other directory if enabled)",
              lines=5, max_lines=400, value="", scale=6
            )
            booru_pattern_blacklist = gr.Textbox(
              label="Caption Blacklist Patterns",
              placeholder="Enter caption patterns to blacklist, separated by lines",
              info="if this pattern matches the caption, the image will be skipped (or saved at other directory if enabled)",
              lines=5, max_lines=10000, value="", scale=6
            )
          with gr.Row():
            booru_separate_save = gr.Checkbox(
              value=True, label="Blacklisted Save Option",
              info="If enabled, blacklisted images will be saved to separate directory", scale=10
            )
            booru_blacklist_save_dir = gr.Textbox(
              label="Blacklisted Save Directory",
              placeholder="Enter the blacklisted save directory",
              value=os.path.join(shared.api_path, "C:/Users/luna_/Pictures/blacklisted"), scale=19
            )
            booru_blacklist_browse_dir = gr.Button(
              "📁", variant="secondary", scale=1
            )
            booru_blacklist_browse_dir.click(
              fn=select_folder,
              outputs=[booru_blacklist_save_dir]
            )

        with gr.Accordion(label="Advanced Settings", open=False):
          with gr.Row():
            with gr.Group():
              with gr.Row():
                enable_stop = gr.Checkbox(
                  label="Enable Auto-Stop",
                  value=False, info="Enable stop generation after options", 
                )
                stop_mode = gr.Dropdown(
                  choices=["After Minutes", "After Images", "At Datetime"],
                  value="After Minutes", label="Stop Mode",
                )
              with gr.Row():
                stop_after_minutes = gr.Number(
                  label="Stop After Minutes",
                  value=240, precision=0, step=1
                )
                stop_after_images = gr.Number(
                  label="Stop After n of Images",
                  value=0, precision=0, step=1
                )
                stop_after_datetime = gr.Textbox(
                  label="Stop At Datetime",
                  value="2025-07-24 00:07:24", placeholder="YYYY-MM-DD HH:MM:SS"
                )
      with gr.Row():
        with gr.Accordion(label="Output Options", open=False):
          with gr.Row():
            output_dir = gr.Textbox(
              label="Output Directory",
              placeholder="Enter the output directory",
              value=os.path.join(shared.api_path, "outputs/txt2img-images/{DATE}-pem"),
              lines=1, max_lines=1, scale=19
            )
            browse_dir = gr.Button(
              "📁", variant="secondary",
              scale=1
            )
            browse_dir.click(
              fn=select_folder,
              outputs=[output_dir]
            )
          with gr.Row():
            output_format = gr.Dropdown(
              choices=["PNG", "JPEG", "WEBP"],
              label="Output Format", value="PNG",
              scale=6
            )
            output_name = gr.Textbox(
              label="Output Name",
              placeholder="Enter the output name",
              value="{image_count}-{seed}.{ext}",
              lines=1, max_lines=1, scale=4
            ) 
          with gr.Row():
            save_metadata = gr.Checkbox(
              value=True, label="Save Metadata",
              info="If enabled, metadata will be saved in the output image"
            )
            save_infotext = gr.Checkbox(
              value=True, label="Save Infotext",
              info="If enabled, infotext will be saved as .txt"
            )
              
        with gr.Accordion(label="Regional Prompter", open=False):
          pass # TODO: implement
        
      with gr.Row():
        skip_img = gr.Button("Skip Image", variant="secondary", scale=7)
        skipped_img = gr.Checkbox(
          value=False, label="Skipped", interactive=False,
        )
        skip_img.click(
          fn=instance.skip_image,
          inputs=[],
          outputs=[skipped_img]
        )
        
      generate = gr.Button("Start", variant="primary")
      stop = gr.Button("Stop", variant="primary", )
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
      
      save_all_param = gr.Button(
        "Save current parameters",
        variant="secondary"
      )
      var = [
          lora, blacklist, pattern_blacklist,
          blacklist_multiplier, use_relative_freq,
          w_multiplier, w_min, w_max,
          disallow_duplicate, header, footer,
          max_tags, base_chance, add_lora_name, lora_weight,
          s_method, scheduler, steps_min, steps_max,
          cfg_min, cfg_max, batch_count, batch_size,
          size, adetailer, enable_hand_tap,
          disable_lora_in_adetailer, enable_freeu, preset, negative,
          enable_stop, stop_mode, stop_after_minutes,
          stop_after_images, stop_after_datetime,
          output_dir, output_format, output_name,
          save_metadata, save_infotext,
          booru_filter_enable, booru_model,
          booru_threshold, booru_character_threshold,
          booru_allow_rating, booru_ignore_questionable,
          booru_save_each_rate, booru_merge_sensitive,
          general_save_dir, sensitive_save_dir,
          questionable_save_dir, explicit_save_dir,
          booru_blacklist, booru_pattern_blacklist,
          booru_separate_save, booru_blacklist_save_dir,
      ]
      generate.click(
        fn=instance.start,
        inputs=var,
        outputs=[eta, progress, progress_bar_html, image, output]
      )
      stop.click(
        fn=instance.stop_generation,
        inputs=[],
        outputs=[]
      )

      save_all_param.click(
        fn=None, # TODO
        inputs=var,
      )