import random

from modules.calculator.inference import PromptInferenceEngine
from modules.forever.common2 import ForeverGenerationTemplate
import gradio as gr

from modules.utils.prompt import combine_prompt
from modules.utils.util import rndrange

class ForeverGenerationFromData(ForeverGenerationTemplate):
  def __init__(self, payload = None):
    super().__init__({})
    self.instance_name = "from Data"
  
  def on_reset(self):
    if hasattr(self, "engine") and self.engine is not None: del self.engine
    self.engine: PromptInferenceEngine = None
    self.top_k = [] # min, max
    self.temperature = 1.0
    self.sim_thres = []
    self.target_rating = []
    self.rating_str = []
    self.force_rating = []
    self.negative_strength = []
    self.strict_negative = False
    self.negative_thres = []
    self.append_always_prompt = False
    
    self.input_data = []
    self.input_negatives = []
  
  async def on_update_prompt_settings(
    self, 
    datapath, init_data_tags, init_data_negative,
    temperature_min, temperature_max, top_k_min, top_k_max, sim_thres_min, sim_thres_max, append_always_prompt,
    negative_strength_min, negative_strength_max, negative_thres_min, negative_thres_max, strict_negative,
    data_rating, rating_strength_min, rating_strength_max, rating_force_bias_min, rating_force_bias_max, 
    **kw
  ):
    try:
      self.engine = PromptInferenceEngine(datapath)
    except FileNotFoundError:
      raise gr.Error(f"Data file not found: {datapath}")
    self.input_data = init_data_tags.split(",")
    if self.input_data == [""] or len(self.input_data) == 0:
      raise gr.Error("Initial tags cannot be empty!")
    self.input_negatives = init_data_negative.split(",")
    self.temperature = [temperature_min, temperature_max]
    self.top_k = [top_k_min, top_k_max]
    self.sim_thres = [sim_thres_min, sim_thres_max]
    self.append_always_prompt = append_always_prompt
    self.negative_strength = [negative_strength_min, negative_strength_max]
    self.negative_thres = [negative_thres_min, negative_thres_max]
    self.strict_negative = strict_negative
    
    self.target_rating = data_rating
    self.rating_str = [rating_strength_min, rating_strength_max]
    self.force_rating = [rating_force_bias_min, rating_force_bias_max]
  
  async def get_payload(self):
    p = await self._get_payload()
    p["prompt"] = self.combine_header_footer(
        self.engine.generate_prompt(
          self.input_data, 
          self.input_negatives,
          rndrange(self.temperature),
          rndrange(self.top_k),
          rndrange(self.sim_thres),
          random.choice(self.target_rating),
          rndrange(self.rating_str),
          rndrange(self.force_rating),
          float("-inf") if self.strict_negative else rndrange(self.negative_strength),
          rndrange(self.negative_thres),
          self.append_always_prompt
        )
      )
    return p