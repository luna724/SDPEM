import gradio as gr
from typing import *
from v4.lunapy_module_importer import Importer, Importable

generatorTypes = Importer("modules.types", isTypes="generator")
class g(generatorTypes):
  class Tweaking:
    def __init__(self, template: dict):
      self.t = template
    
    def __call__(self, key: str) -> Any:
      try:
        return self.t[key]
      except KeyError:
        return None
      except IndexError:
        return None
  
  def compare_addons(self, var):
    return
    
      
  def __init__(self):
    super().__init__()
    self.get_templates = self.generate_common.obtain_template_list
    self.get_lora = self.generate_common.obtain_lora_list
    self.ui_config = self.config.get_spec_value("user_variable.ui.system")
    self.shortcut_via:dict = self.config.get_spec_value("system.generate.custom_buildin_shortcut_via")
    self.addon_utils = Importer("modules.addon")
    
    self.selected_template:str = None
    self.selected_lora:str = None
    
    # Template
    self.blank_template = gr.update(interactive=False, label="")
    
    
    # Temporary Variable
    self.lora_template_v5_from_above = ["v5"]
    self.getAny = { 
      "?AnyLoRA": [],
      "?AnyName": [],
      "?AnyPrompt": [],
      "$FACE": [],
      "$LOCATION": [],
      "$ACCESSORY": [],
      "$OTHER": [],
      "$LV1": [],
      "$LV2": []
    }
  
  def convert_old_method(self, prompt:str) -> str:
    # getAny の更新
    self.shortcut_via = self.config.get_spec_value("system.generate.custom_buildin_shortcut_via")
    
    for i, (_, values) in enumerate(self.shortcut_via.items()):
        key = list(self.getAny.keys())[i]
        self.getAny[key] = values
    
    prompts = self.lib.prompt_converter(prompt)
    new_prompts = prompts.copy()
    
    # # デバッグメッセージ
    # print(f"[DEBUG]: 初期プロンプト: {prompts}")
    # print(f"[DEBUG]: 変換対象: {self.getAny}")
    
    for index, p in enumerate(prompts):
      for converted, triggers in self.getAny.items():
        if self.lib.delete_weights(p) in triggers:
          new_prompts[index] = converted
          print(f"[INFO]: {p} -> {converted}")
    
    return self.lib.prompt_converter(new_prompts)
  
  def generate(self,
    template_key, lora_key, lora_weight, extend_lora_enable, enable_adetailer_lora,
    enable_negative_lora, realtime_infer, tmpl_prompt, tmpl_negative,
    use_prompt_nsfw_mode, lora_var_1, lora_var_2,
    face, face2, location, location2, accessory, other_variable, header, lower
    ) -> Tuple[str, str, str, str]:
      """ Return tuple (len==4)"""
      def replacing(prompt:str, var:List[str], rpTo:str) -> str:
        """ return prompt like str"""
        prompts = self.lib.prompt_converter(prompt, ",")
        rpCount = prompts.count(rpTo)
        
        for index, p in enumerate(prompts):
          if p == rpTo:
            if rpCount == 1:
              prompts[index] = f"{var[0]}, {var[1]}"
            else:
              if var == []:
                _ = prompts.pop(index)
                continue
              prompts[index] = var.pop(0)
        
        return self.lib.prompt_converter(prompts, ", ")
      
      def define_r():
        def r(x:str) -> str:
          """ resize(), delete comma and space from header/lower"""
          if not isinstance(x, str):
            print("[ERR]: R() got unknown types input: ", x, "\n", "Instance: ", type(str))
          
          return x.strip().strip(",")
        return r
      
      r = define_r()
      
      # Error handling
      if lora_key == "":
        raise gr.Error("can't find that LoRA")

      template, template_ver = self.get_templates.get_template_value(template_key)
      _, lora, name, ch_prompt, ch_extend, lv1, lv2, loraislora = self.get_lora.manual(True, lora_key)
      
      v = template["Values"]
      v_get = self.Tweaking(v)
      
      prompt = self.convert_old_method(v_get("Prompt"))
      negative = self.convert_old_method(v_get("Negative"))
      ad_prompt = self.convert_old_method(v_get("AD_Prompt"))
      ad_negative = self.convert_old_method(v_get("AD_Negative"))

      lora = self.lib.control_lora_weight(lora, lora_weight, loraislora)
      if extend_lora_enable:
        if not isinstance(ch_extend, str):
          print("[WARN]: this LoRAs not include extend.")
        else:
          ch_prompt = r(ch_prompt) + ", " + r(ch_extend)
      
      if realtime_infer:
        print("using realtime Infer..")
        prompt = self.convert_old_method(tmpl_prompt)
        negative = self.convert_old_method(tmpl_negative)
      
      if use_prompt_nsfw_mode:
        nsfw_prompt = v_get("NSFW_Prompt")
        if nsfw_prompt is None:
          print("[WARN]: this Templates not incude NSFW Prompt.")
        else:
          prompt = self.convert_old_method(nsfw_prompt)
      
      prompt1 = self.lib.multiple_replace(
        prompt, [
          ("?AnyLoRA", r(lora)), ("?AnyName", r(name)),
          ("?AnyPrompt", r(ch_prompt))
        ]
      )
      
      # face, location, other
      lvk = ([r(face), r(face2)], [r(location), r(location2)])
      lvv = ("$FACE", "$LOCATION")
      
      for (var, rpto) in zip(lvk, lvv):
        prompt1 = replacing(
          prompt1, var, rpto
        )
      
      lvk = ("$ACCESSORY", "$OTHER")
      lvv = (r(accessory), r(other_variable))
      for (rpto, var) in zip(lvk, lvv):
        prompt1 = self.lib.replace_variable(
          prompt1, rpto, var
        )
      
      ### TODO: prompt keyword 変換の実装
      # LoRA Variables
      lv1_info = ""
      lv2_info = ""
      if lv1[0]:
        lv1_info = lv1[2]
      if lv2[0]:
        lv2_info = lv2[2]
      
      lvk = ("$LV1", "$LV2")
      lvv = (r(lv1_info), r(lv2_info))
      for (x, y) in zip(lvk, lvv):
        prompt1 = self.lib.replace_variable(
          prompt1, x, y
        )
      
      prompt1 = self.lib.prompt_head_low(prompt1, header, lower)
      prompt1 = self.lib.comma_tweak(prompt1)
      
      # ADetailer prompt resize
      if not enable_adetailer_lora:
        def r(*x): return ""
        
      lvk =("?AnyLoRA", "?AnyName", "?AnyPrompt", "$ACCESSORY", "$OTHER")
      lvv = (r(lora), r(name), r(ch_prompt), r(accessory), r(other_variable))
      for (x, y) in zip(lvk, lvv):
        ad_prompt = self.lib.replace_variable(
          ad_prompt, x, y
        )
      
      if lv1[0]:
        lv1_info = r(lv1[2])
      if lv2[0]:
        lv2_info = r(lv2[2])
      
      for (x, y) in zip(("$LV1", "$LV2"), (lv1_info, lv2_info)):
        ad_prompt = self.lib.replace_variable(
          ad_prompt, x, y
        )
      
      lvk = ([r(face), r(face2)], [r(location), r(location2)]),
      lvv = ("$FACE", "$LOCATION")
      
      for (x, y) in zip(lvk, lvv):
        ad_prompt = replacing(
          ad_prompt, x, y
        )
      
      r = define_r()
      # Negative prompt resize
      if not enable_negative_lora:
        def r(*x): return ""
      
      lvk = (
          "?AnyLoRA", "?AnyName", "?AnyPrompt", 
          "$ACCESSORY", "$OTHER"
        )
      lvv = (
          r(lora), r(name), r(ch_prompt), r(accessory), r(other_variable)
        )
      for (x, y) in zip(lvk, lvv):
        negative = self.lib.replace_variable(
          negative, x, y
        )
      
      for (x, y) in zip(("$LV1", "$LV2"), (lv1_info, lv2_info)):
        negative = self.lib.replace_variable(
          negative, x, y
        )
        
      lvk = ([r(face), r(face2)], [r(location), r(location2)]),
      lvv = ("$FACE", "$LOCATION")
      for (x, y) in zip(lvk, lvv):
        negative = replacing(
          negative, x, y
        )
      
      # アドオン
      self.compare_addons([prompt1, negative, ad_prompt, ad_negative])
      
      return prompt1, negative, ad_prompt, ad_negative

  def generate_paster(
      self, *arg
    ) -> str:
    prompt, negative, ad_prompt, ad_negative = self.generate(
      *arg
    )
    
      

class generate(Importable):
  def __call__(self, **kwargs):
    return g()