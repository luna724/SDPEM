import gradio as gr
from gradio.components import Component
from typing import Optional, Literal

from modules.utils.ui.register import RegisterComponent, ValuesMap
from modules.utils.ui.utils import range_check
from utils import error

class rWrapper:
  def __init__(self, r: "RegisterComponent.register", disc: str):
    self.r = r
    self.i = r(objName=True)
    self.registered = []
    
    self.disc = disc
    
  def __call__(self, key, comp):
    if isinstance(comp, Component):
      comp.elem_id = f"{self.i}.{self.disc}^{key}"
      self.r(key, comp)
      self.registered.append(comp.elem_id)
    elif isinstance(comp, dict):
      for k, c in comp.items():
        self.r(k, c)
    else:
      error(f"Invalid component type for key '{key}' in template definition.")

class _templates:
  # return rWrapper: 静的描画関数, r, defaultを必ず受け取る
  # return dict: 動的描画関数, TabContent.renderで描画される
  async def sd_params(r, default, **k):
    from modules.sd_param import get_sampler, get_scheduler
    r = rWrapper(r, "sd_params")
    with gr.Accordion(label="Parameter Settings", open=False):
      with gr.Row():
        s_method = r(
          "s_method",
          gr.Dropdown(
              choices=await get_sampler(),
              label="Sampling Methods",
              value=default.s_method or ["Euler a"],
              multiselect=True,
              scale=6,
          ),
        )
        scheduler = r(
          "scheduler",
          gr.Dropdown(
              choices=await get_scheduler(),
              label="Scheduler",
              value=default.scheduler or ["Automatic"],
              multiselect=True,
              scale=4,
          ),
        )
      with gr.Row():
        with gr.Column():
          steps_min = r(
            "steps_min",
            gr.Slider(
                1,
                150,
                step=1,
                value=default.steps_min or 20,
                label="Min Sampling Steps",
            ),
          )
          steps_max = r(
            "steps_max",
            gr.Slider(
                1,
                150,
                step=1,
                value=default.steps_max or 60,
                label="Max Sampling Steps",
            ),
          )
          steps_min.input(
            range_check, inputs=[steps_min, steps_max], outputs=[steps_min, steps_max], show_progress=False
          )
          steps_max.input(
            range_check, inputs=[steps_min, steps_max], outputs=[steps_min, steps_max], show_progress=False
          )
          
        with gr.Column():
          cfg_min = r(
            "cfg_min",
            gr.Slider(
                0.1,
                30,
                step=0.1,
                value=default.cfg_min or 5,
                label="Min CFG Scale",
            ),
          )
          cfg_max = r(
            "cfg_max",
            gr.Slider(
                0.1,
                30,
                step=0.1,
                value=default.cfg_max or 7,
                label="Max CFG Scale",
            ),
          )
          cfg_min.input(
            range_check, inputs=[cfg_min, cfg_max], outputs=[cfg_min, cfg_max], show_progress=False
          )
          cfg_max.input(
            range_check, inputs=[cfg_min, cfg_max], outputs=[cfg_min, cfg_max], show_progress=False
          )
          
        with gr.Row():
          r(
            "batch_count",
            gr.Number(
                label="Batch Count",
                value=default.batch_count or 1,
                precision=0,
            ),
          )
          r(
            "batch_size",
            gr.Number(
                label="Batch Size",
                value=default.batch_size or 2,
                precision=0,
            ),
          )

      r(
          "size",
          gr.Textbox(
              label="Image Size(s) (w:h,w:h,...) (separate by commas)",
              placeholder="e.g. 896:1152,1024:1024,1152:896",
              value=default.size or "896:1152,1024:1024,1152:896",
          ),
      )
      
      with gr.Accordion(label="ADetailer (Simplified)", open=False):
        r(
          "adetailer",
          gr.Checkbox(
              value=default.adetailer,
              label="Enable ADetailer with Template",
              info="Enable ADetailer for image generation",
          ),
        )
        r(
          "enable_hand_tap",
          gr.Checkbox(
              value=default.enable_hand_tap,
              label="Enable Hand Restoration",
              info="Enable hand_yolov8s.pt detector",
          ),
        )
        r(
          "disable_lora_in_adetailer",
          gr.Checkbox(
              value=default.disable_lora_in_adetailer,
              label="Disable LoRA Trigger in ADetailer",
              info="If enabled, LoRA trigger (<lora:name:.0>) will not be applied in ADetailer",
          ),
        )
      with gr.Accordion(
        label="FreeU (Integrated for ForgeUI)", open=False
      ):
        r(
          "enable_freeu",
          gr.Checkbox(
              value=default.enable_freeu,
              label="Enable FreeU",
              info="Enable FreeU for image generation",
          ),
        )
        r(
          "preset",
          gr.Dropdown(
              choices=["SDXL", "SD 1.X"],
              label="FreeU Preset",
              value=default.preset or "SDXL",
          ),
        )
      
      with gr.Accordion(
        label="SelfAttentionGuidance (Integrated for ForgeUI)", open=False
      ):
        r(
          "enable_sag",
          gr.Checkbox(
              value=default.enable_sag,
              label="Enable SelfAttentionGuidance",
              info="Enable SelfAttentionGuidance for image generation",
          ),
        )
        r(
          "sag_strength",
          gr.Slider(
              minimum=0.0,
              maximum=1.0,
              step=0.01,
              label="SelfAttentionGuidance Strength",
              value=default.sag_strength or 0.55
          ),
        )
    return r

  

# type-hint (変更、実用禁止)
class uiStructure:
  # shouldbe unique, NOT startwith("_") and == "component"
  component_name: Optional[Component | dict[str, Component] | list[str,dict] | list[list[str,dict]]]
  
  # should be startwith _ and following getattr(gr, key)
  _key: dict[Optional[
    Literal["row", "column", "accordion", "tabs"]
  ] | str, "uiStructure"]
  """
  example
  {
    "_row": {
      "component": ["input_box", "Textbox", {"label": "Input"}],
      "_column": {
        "_kw": {"scale": 2},
        "submit": gr.Button(),
        "_accordion": {
          "component": {"result": gr.Checkbox(), "result_thres": gr.Slider()}
        }
      }
    }
  }
  """

class TabContent:
  def __init__(self, ui: dict | uiStructure, error_hint: str = "tab"):
    self.ui: dict = ui
    self.n = error_hint
    
  @classmethod
  async def render_tmpl(cls, template_name: str, r: RegisterComponent, default: ValuesMap, error_hint: str = "tab", tmpl_args: dict = None):
    tmpl_args = tmpl_args or {}
    tmpl_args["r"] = r
    tmpl_args["default"] = default
    tmpl = await getattr(_templates, template_name)(**tmpl_args)
    if tmpl is None or isinstance(tmpl, rWrapper):
      return tmpl
    
    c = cls(tmpl, error_hint)
    c.render(r, default)
  
  def render(self, r: RegisterComponent, default: ValuesMap) -> None:
    registered = []
    def proc_nest(ui, nest_i = 0):
      def proc_list_component(key: str, item: dict, index):
        # [key, comp_key, comp_kw] (list[str,dict])
        if not hasattr(gr, item[1]):
          error(f"Invalid component '{item[1]}' for key '{key}' in {self.n} definition. ({nest_i}-{index})")
          return
        if "value" in item[2]:
          v = getattr(default, key) 
          item[2]["value"] = item[2]["value"] if v is None else v
        comp = getattr(gr, item[1])(**item[2])
        r(item[0], comp)
        registered.append(item[0])
        
      # key: compを処理
      for index, (key, nest) in enumerate(ui.items()):
        key = key.strip()
        
        if key.startswith("_"):
          if not hasattr(gr, key[1:]):
            error(f"Invalid layout component '{key}' in {self.n} definition. ({nest_i}-{index})") # TODO: 1-2-4 のようなネストへの対応
            continue
          wid = getattr(gr, key[1:])
          with wid(**nest.pop("_kw",{})):
            proc_nest(nest, nest_i + 1)
            
        else:
          if key != "component" and key in registered:
            error(f"Duplicate component key '{key}' in {self.n} definition. ({nest_i}-{index})")
            continue
          
          if isinstance(nest, Component):
            r(key, nest)
            registered.append(key)
            
          elif isinstance(nest, dict):
            # {"key": comp, ..} (dict[str,Component])
            proc_nest(nest, nest_i) # pass
          
          elif isinstance(nest, list):
            if isinstance(nest, list):
              for i, item in enumerate(nest): # list[list..]
                if key.lower() == "component" and len(item) == 3 and isinstance(item[0], str):
                  proc_list_component(key, item, f"{index}-{i}")
                else:
                  error(f"Invalid list component definition for key '{key}' in {self.n} definition. ({nest_i}-{index}-{i})")
            elif key.lower() == "component" and len(nest) == 3 and isinstance(nest[0], str):
              proc_list_component(key, nest, index)
            else:
              error(f"Invalid list component definition for key '{key}' in {self.n} definition. ({nest_i}-{index})")
          
          else:
            error(f"Invalid component definition for key '{key}' in {self.n} definition. ({nest_i}-{index})")
            continue
    proc_nest(self.ui)