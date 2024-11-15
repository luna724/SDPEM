from v4.lunapy_module_importer import Importer, Importable
from typing import *
import re

generatorTypes = Importer("modules.types", isTypes="generator")
class Character_Exchanger(generatorTypes):
  def __init__(self):
    super().__init__()
    self.method_version = self.config.get_spec_value("script_version.call_api.ce")
  
  @staticmethod
  def get_module_name():
    return "cev4"
  
  def v3(self, base_mode, prompt, lora_template, for_template, *args):
    ### Compatibility for v4    
    if "lora, name" in base_mode:
      mode = ["lora", "name"]
    else:
      mode = []
    if "prompt" in base_mode:
      mode.insert(0, "prompt")
    if "extend" in base_mode:
      print("[WARNING]: CEv3 has not compatibility with 'Extend exchange'.")
    
    args = None 
    lora_list = [
      (x[0].split(":")[0]+":"+x[0].split(":")[1]+":", x[1], x[2])
      for x in self.generate_common.obtain_lora_list.only_lora()
      ]
    
    prompt_lora = self.lib.re4prompt(r"(<lora:.*:).*>", prompt)
    target = None
    name = None
    
    # LoRAリストにマッチするものを検出
    for lora in prompt_lora:
      for tpl in lora_list:
        if tpl[0] in lora:
          target = tpl[0]
          key = tpl[1]
          
          try:
            prompt_name = self.lib.re4prompt(tpl[2], prompt)
            name = prompt_name[0]
            target = tpl[0]
            break
          except IndexError:
            continue
    if for_template:
      mode = ["prompt", "lora", "name"]
    
    if name == None or target == None:
      raise ValueError("LoRA Template cannot found.")
    
    loraname = re.findall(r"<lora:(.*):", target)[0]
    lora_weight = self.lib.re4prompt(rf"<lora:{loraname}:(.*)>", prompt)[0]
    
    prompt = re.sub(rf"<lora:{loraname}:{lora_weight}>", "$LORA", prompt, count=1)
    key, _, name, ch_prompt, extend, lv1, lv2, loraislora = self.generate_common.obtain_lora_list.manual(True, key)
    target_key, target_lora, target_name, target_prompt, target_extend, lv1, lv2, loraislora = self.generate_common.obtain_lora_list.manual(
      True, lora_template
    )
    if not "lora" in mode:
      target_key = key
    
    if "name" in mode:
      prompt = re.sub(
        rf"{name},", "$NAME,", prompt, count=1
      )
    # re4prompt を使用し、prompt から ch_prompt を摘出
    # ひとつづつ対象のキャラの prompt に変換
    if for_template:
      mode = ["prompt"]
      target_prompt = "$PROMPT"
    
    if "prompt" in mode:
      prompts = []
      for p in prompt.split(","):
        for x in  ["(", ")", "[", "]", ""]:
          p = p.strip().strip(x)
        
        if re.findall(r":(\d+\.\d+)", p):
          if p.count(">") > 0:
            pass
          # else:
          #   p = re.sub(r"(:\d+\.\d+)", "", p, count=1)
          
        prompts.append(p)
      
      if target_prompt.count(",") < 1:
        target_prompts = [target_prompt.strip()]
      else:
        target_prompts = [
          p.strip() for p in target_prompt.split(",")]
      if ch_prompt.count(",") < 1:
        ch_prompts = [ch_prompt.strip()]
      else:
        ch_prompts = [
          p.strip() for p in ch_prompt.split(",")]
      
      cp_indexes = []
      for p in prompts:
        if p in ch_prompts:
          index = prompts.index(p)
          cp_indexes.append((index, p))

      # if len(cp_indexes) != len(ch_prompts):
      #   raise ValueError("cannot find character name")

      for running, (i, text) in enumerate(cp_indexes):
        replaceTo = self.lib.get_index(
          target_prompts, running, "$LPY-fAILEVENT"
        )
        if replaceTo == "$LPY-fAILEVENT":
          prompts[i] = "#PASS"
        else:
          prompts[i] = replaceTo
        
        last = (running, i)
      
      if not len(target_prompts) == last[0]:
        # prompts を分割、最後の ch_prompts の位置にすべて残りを突っ込む
        prompt1 = prompts[:last[1]+1]
        prompt2 = prompts[last[1]+1:]
        
        for x in target_prompts[last[0]+1:]:
          prompt1.append(x)
        
        prompts = prompt1 + prompt2
      
      prompt = ""
      for x in prompts:
        if x == "#PASS":
          continue
        prompt += str(x)+", "
    if for_template:
      while prompt.count(", , ") >= 1:
        prompt = prompt.replace(", , ", ", ")
    
      return prompt, f"converted: -> Template mode"
    prompt = self.generation_finalizer.finalize(prompt, (target_key, (lora_weight, 1.0)))
    
    while prompt.count(", , ") >= 1:
      prompt = prompt.replace(", , ", ", ")
    
    return prompt, f"Detected: {key} -> {target_key}"
    
  def call(self, rt, prompt, lora_template, for_template):
    # Current latest version: V3
    # Current Available version: [v3]
    version_list = {
      "v3-stable": self.v3,
      "v4b1": None
    }
    return version_list[self.method_version](rt, prompt, lora_template, for_template)
    
    
class character_exchanger_api_main(Importable):
  def __call__(self, **kwargs):
    return Character_Exchanger()