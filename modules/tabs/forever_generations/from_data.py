import gradio as gr
from pathlib import Path
from typing import Callable

from modules.sd_param import get_sampler, get_scheduler
from modules.utils.browse import select_file
from modules.utils.ui.register import RegisterComponent
from modules.utils.ui.templates import TabContent
from webui import UiTabs
class DataToPrompt(UiTabs):
  def title(self) -> str:
    return "from Data"

  def index(self) -> int:
    return 2

  async def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
    r = RegisterComponent(
      Path("./defaults/forever_generation.from_data.json"),
      "forever_generation/from_data",
    )
    default = r.get()

    def create_minmax(
      r, key, label, step, min, max, min_def, max_def= None,info=None,
      **kw
    ):
      if max_def is None: max_def = min_def
      return r(key+"_min",gr.Slider(
        label=label+" min",
        value=default(key+"_min", min_def),
        step=step,
        info=info,
        minimum=min,maximum=max, **kw
      )), r(key+"_max",gr.Slider(
          label=label+" max",
          value=default(key+"_max", max_def),
          step=step,
          minimum=min,maximum=max, **kw
      ))
      
    with gr.Blocks():
      with gr.Row():
        datapath = r(
          "datapath",
          gr.Textbox(
            label="Data filepath",
            value=default("datapath", "data/eg.json"),
            scale=6,
          ),
        )
        browse_btn = gr.Button("Browse", variant="secondary")
        browse_btn.click(fn=select_file, outputs=datapath, show_progress=False)
      
      with gr.Row():
        init_data_tags = r(
          "init_data_tags",
          gr.Textbox(
          label="Initial tags",
          info="Comma-separated base tags that will be preserved",
          placeholder="tag1, tag2",
          lines=2,
          max_lines=4,
          value=default("init_data_tags", ""),
          ),
        )
        init_data_negative = r(
          "init_data_negative",
          gr.Textbox(
          label="Initial negative tags",
          info="Comma-separated negatives",
          value=default ("init_data_negative", "worst quality, 1boy"),
          lines=2,
          max_lines=4,
          ),
        )

      with gr.Row():
        with gr.Column():
          with gr.Row():
            temperature_min, temperature_max = create_minmax(
              r, "temperature", "Temperature", 0.05, 0.05, 2, 1, info="Softmax temperature for sampling; lower = pick top scores",
            )
          
          with gr.Row():
            top_k_min, top_k_max = create_minmax(
              r, "top_k", "tag counts (Top-k)", 1, 0, 100, 10, info="How many tags to consider/sample per round",
            )
            
          with gr.Row():
            sim_thres_min, sim_thres_max = create_minmax(
              r, "sim_thres", "Similarity threshold", 0.01, 0, 1, 0.7, info="Reject new tags that are too similar to selected ones",
            )

          append_always_prompt = r(
            "append_always_prompt",
            gr.Checkbox(
            label="Append always-on tags",
            info="Keep the engine's always_tag entries",
            value=default("append_always_prompt", False),
            ),
          )
          
          
        with gr.Column():
          with gr.Row():
            negative_strength_min, negative_strength_max = create_minmax(
              r, "negative_strength", "Negative bias strength", 0.05, 0, 10, 1, info="Finite penalty factor; ignored when strict negative drop is on",
            )
          with gr.Row():
            negative_thres_min, negative_thres_max = create_minmax(
              r, "negative_thres", "Negative similarity threshold", 0.01, 0, 1, 0.05, info="Above this PMI with negatives the penalty triggers",
              scale=4
            )
            strict_negative_input = r(
              "strict_negative",
              gr.Checkbox(
                label="Drop conflicting negatives",
                info="Match engine default: skip tags tied to negatives by using infinite penalty",
                value=default("strict_negative", True),
              ),
            )
          
          data_rating = r(
            "data_rating",
            gr.Dropdown(
            label="Target rating",
            info="Bias suggestions toward the dataset rating bucket (random from selected)",
            choices=["general", "sensitive", "explicit"],
            value=default("data_rating", ["general", "sensitive", "explicit"]),
            multiselect=True,
            ),
          )
          
          with gr.Row():
            rating_strength_min, rating_strength_max = create_minmax(
              r, "rating_strength", "Rating bias strength", 0.05, 0, 10, 1, info="How strongly to bias toward the target rating",
            )
          with gr.Row():
            rating_force_bias_min, rating_force_bias_max = create_minmax(
              r, "rating_force_bias", "Force rating bias", 0.01, 0, 10, 0, info="How strongly to force the target rating (vs just biasing it)",
            )
          