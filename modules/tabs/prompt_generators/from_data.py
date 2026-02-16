from pathlib import Path
from modules.calculator.training import train
from modules.utils.prompt import combine_prompt
from modules.utils.ui.register import RegisterComponent
from webui import UiTabs
import gradio as gr
from typing import Callable
from modules.utils.browse import select_file, select_folder, select_folders
from modules.calculator.inference import PromptInferenceEngine

class LoRAToPrompt(UiTabs):
  def title(self) -> str:
    return "from data"
  def index(self) -> int:
    return 2
  def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
    rc = RegisterComponent(Path("./defaults/prompt_generator.from_data.json"), "prompt_generators/from_data")
    r = rc.register
    default = rc.get()

    def d(key, fallback):
      val = getattr(default, key, None)
      return fallback if val is None else val

    async def generate_prompt(
      datadir, inputs, header, footer, temp, top_k, sim_thres, append_always_prompt,
      rating, rating_str, force_rating, negative, negative_strength, negative_thres, strict_negative,
    ) -> str:
      try:
        engine = PromptInferenceEngine(datadir)
      except FileNotFoundError as e:
        return str(e)
      
      res = engine.generate_prompt(
        inputs.split(","),
        init_negatives=negative.split(","),
        temperature=temp,
        top_k=top_k,
        similarity_threshold=sim_thres,
        target_rating=rating,
        rating_strength=rating_str,
        force_rating=force_rating,
        negative_strength=float("inf") if strict_negative else negative_strength,
        negative_threshold=negative_thres,
        append_always_tags=append_always_prompt,
      )
    
      return combine_prompt(header, res, footer)
  
    with gr.Blocks():
      with gr.Row():
        datapth = r(
          "datapth",
          gr.Textbox(
          label="Data filepath (generate/train will look here)",
          value=d("datapth", "data/eg.json"),
          scale=8,
          ),
        )
        browse_btn = gr.Button("Browse", scale=2, variant="secondary")
        browse_btn.click(
          fn=select_file, outputs=datapth
        )
      
      def define_generator(r):
        with gr.Accordion(label="Generator", open=False):
          with gr.Row():
            init = r(
              "init",
              gr.Textbox(
              label="Initial tags",
              info="Comma-separated base tags that will be preserved",
              placeholder="tag1, tag2",
              lines=2,
              max_lines=4,
              value=d("init", ""),
              ),
            )
            init_neg = r(
              "init_neg",
              gr.Textbox(
              label="Initial negative tags",
              info="Comma-separated negatives (defaults mirror engine defaults)",
              value=d("init_neg", "worst quality, 1boy"),
              lines=2,
              max_lines=4,
              ),
            )
          
          with gr.Row():
            rating = r(
              "rating",
              gr.Dropdown(
              label="Target rating",
              info="Bias suggestions toward the dataset rating bucket",
              choices=["general", "sensitive", "explicit"],
              value=d("rating", "general"),
              multiselect=False,
              ),
            )
            rating_str = r(
              "rating_str",
              gr.Slider(
              label="Rating strength",
              info="How strongly to bias toward the selected rating (engine default 1.0)",
              minimum=0.0,
              maximum=2.0,
              value=d("rating_str", 1.0),
              step=0.05,
              ),
            )
            force_rating = r(
              "force_rating",
              gr.Slider(
              label="Force rating bias",
              info="Increase to push closer to the target rating probability (engine default 0)",
              minimum=0.0,
              maximum=1.0,
              value=d("force_rating", 0.0),
              step=0.05,
              ),
            )
          
          with gr.Row():
            with gr.Column():
              temp = r(
                "temp",
                gr.Slider(
                label="Temperature",
                info="Softmax temperature for sampling; lower = pick top scores (engine default 1.0)",
                minimum=0.05,
                maximum=2.0,
                value=d("temp", 1.0),
                step=0.05,
                ),
              )
              top_k = r(
                "top_k",
                gr.Slider(
                label="Top-K (Tag count w/o always-on tags)",
                info="How many tags to consider/sample per round (engine default 10)",
                minimum=1,
                maximum=50,
                value=d("top_k", 10),
                step=1,
                ),
              )
            with gr.Column():
              sim_thres = r(
                "sim_thres",
                gr.Slider(
                label="Similarity threshold",
                info="Reject new tags that are too similar to selected ones (engine default 0.7)",
                minimum=0.0,
                maximum=1.0,
                value=d("sim_thres", 0.7),
                step=0.01,
                ),
              )
              append_always_prompt = r(
                "append_always_prompt",
                gr.Checkbox(
                label="Append always-on tags",
                info="Keep the engine's always_tag entries (engine default: enabled)",
                value=d("append_always_prompt", True),
                ),
              )
          
          with gr.Row():
            neg_str = r(
              "neg_str",
              gr.Slider(
              label="Negative penalty strength",
              info="Finite penalty factor; ignored when strict negative drop is on",
              minimum=0.0,
              maximum=5.0,
              value=d("neg_str", 1.0),
              step=0.05,
              ),
            )
            neg_thres = r(
              "neg_thres",
              gr.Slider(
              label="Negative similarity threshold",
              info="Above this PMI with negatives the penalty triggers (engine default 0.05)",
              minimum=0.0,
              maximum=1.0,
              value=d("neg_thres", 0.05),
              step=0.01,
              ),
            )
            strict_negative = r(
              "strict_negative",
              gr.Checkbox(
              label="Drop conflicting negatives",
              info="Match engine default: skip tags tied to negatives by using infinite penalty",
              value=d("strict_negative", True),
              ),
            )
          
            
        with gr.Row():
          header = r(
            "header",
            gr.Textbox(
              label="Header (will be prepended to the generated prompt)",
              value=d("header", ""),
            ),
          )
          footer = r(
            "footer",
            gr.Textbox(
              label="Footer (will be appended to the generated prompt)",
              value=d("footer", ""),
            ),
          )

        generate = gr.Button("Generate prompt", variant="primary")
        output = gr.Textbox(
          label="Generated prompt",
          placeholder="The generated prompt will be displayed here",
          lines=5,
          max_lines=10,
        )
        generate.click(
          fn=generate_prompt,
          inputs=[
            datapth, init, header, footer, temp, top_k, sim_thres, append_always_prompt,
            rating, rating_str, force_rating, init_neg, neg_str, neg_thres, strict_negative,
          ],
          outputs=output,
        )
      define_generator(r)
      
      # train
      with gr.Accordion(label="format Data (train)", open=False):
        dataset_directory = r(
          "dataset_directory",
          gr.Dropdown(
            label="Dataset directories",
            info="Folder(s) containing training images (can specify multiple)",
            value=d("dataset_directory", []),
            multiselect=True,
          ),
        )
        def update_dd(current):
          existing = list(current) if current else []
          selected = select_folders()
          if not selected:
            return gr.update()
          merged = existing + list(selected)
          return gr.update(value=merged, choices=merged)

        dsb = gr.Button("Browse", variant="secondary")
        dsb.click(
          fn=update_dd, inputs=dataset_directory, outputs=dataset_directory
        )
        
        with gr.Row():
          ignore_questionable = r(
            "ignore_questionable",
            gr.Checkbox(
              label="Ignore questionable ratings",
              info="recommended to large datasets with rating-based filtering; will skip samples rated 'questionable' by the engine's predictor (engine default: enabled)",
              value=d("ignore_questionable", True),
            )
          )
          booru_threshold = r(
            "booru_threshold",
            gr.Slider(
              label="Booru tag threshold",
              value=d("booru_threshold", 0.45),
              minimum=0.1, maximum=0.99, step=0.01,
            )
          )
        
        with gr.Row():
          min_cocc = r(
            "min_cocc",
            gr.Number(
              value=d("min_cocc", 250), label="Min conflict occurrences", info=r"recommended 1500<=this for large datasets, 4x of all unique tags for small datasets"
            ),
          )
          cconfidence = r(
            "cconfidence",
            gr.Slider(
              value=d("cconfidence", 0.7), label="Conflict confidence threshold", minimum=0.05, maximum=1.0, step=0.05
            ),
          )
        proc = r(
          "proc",
          gr.Number(
            value=d("proc", -1),
            label="Processes to use (for training; set to -1 to auto-detect)",
          ),
        )
        train_btn = gr.Button("Train database", variant="primary")
        
        train_log = gr.Textbox(label="log", lines=10, max_lines=200, interactive=False)
        train_btn.click(
          fn=train, inputs=[dataset_directory, datapth, min_cocc, cconfidence, proc, ignore_questionable, booru_threshold], outputs=train_log, show_progress="minimal"
        )
        