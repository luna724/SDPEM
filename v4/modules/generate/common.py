from v4.lunapy_module_importer import Importer, Importable
from v4.LGS import jsoncfg
from typing import *
import os
import gradio as gr

collectorTypes = Importer("modules.types", isTypes="collector")

class obtain_lora_list(collectorTypes ):
  def __init__(self):
    super().__init__()
    self.cfg_root = super().get_data_path()
  
  def initialize(self):
    self.lora_raw = jsoncfg.read(
      os.path.join(self.cfg_root, "lora_template.json")
    )
  
  def manual(self, parse:bool=False, name:str=None, method:None=None, include_version:bool=False) -> Tuple[str, str, str, str, str] | List[str]:
    self.initialize()
    rtl = list(self.lora_raw.keys())
    
    if parse:
      if not name in rtl:
        raise ValueError(f"Failed. {name} isn't in lora_list")
      lora = self.lora_raw[name]
      data = lora[1]
      ver = lora[0]
      
      lora = ""
      name_data = ""
      prompt = ""
      extend = ""
      lora_variables_1 = [False, "", ""]
      lora_variables_2 = [False, "", ""]
      loraislora = True
      
      verList = {"v4": 0, "v5": 1, "v6": 2}
      ver = verList[ver]
      
      if ver >= 0: # v4 and above
        lora = data["lora"]
        name_data = data["name"]
        prompt = data["prompt"]
        extend = data["extend"]
        
        # return name, data["lora"], data["name"], data["prompt"], data["extend"]
      if ver >= 1: # v5 and above
        lv = data["lora_variables"]
        lora_variables_1 = [lv[0][0], lv[1][0][0], lv[1][0][1]]
        lora_variables_2 = [lv[0][1], lv[1][1][0], lv[1][1][1]]
        loraislora = data["loraisLoRA"]
      
      ret = (
        name, lora, name_data, prompt, extend, lora_variables_1, lora_variables_2, loraislora
      )
      if include_version:
        ret += tuple([ver])
      return ret
        
    return rtl
  
  def full(self) -> dict:
    self.initialize()
    return self.lora_raw
  
  def update(self) -> dict:
    self.initialize()
    return gr.update(choices=list(self.lora_raw.keys()))
  
  def only_lora(self) -> List[Tuple[str, str, str]]:
    self.initialize()
    return [
      (self.lora_raw[x][1]["lora"], x, self.lora_raw[x][1]["name"])
      for x in list(self.lora_raw.keys())
    ]

class obtain_template_list(collectorTypes):
  def __init__(self):
    super().__init__()
    self.cfg_root = super().get_data_path()

  def initialize(self):
    self.templates_raw:dict = jsoncfg.read(
      os.path.join(self.cfg_root, "templates.json")
    )
  
  def webui(self) -> list:
    self.initialize()
    return [x["displayName"] for x in self.templates_raw.values()]
  
  def update(self) -> dict:
    values = self.webui()
    return gr.update(choices=values)
  
  def manual(self) -> list:
    self.initialize()
    return list(self.templates_raw.keys())
  
  def full(self) -> dict:
    self.initialize()
    return self.templates_raw
  
  def get_key_by_dn(self, data, target_value) -> list:
    for key, value in data.items():
      if not isinstance(value, dict):
        pass
      if value["displayName"] == target_value:
        return key
    raise ValueError("\nCan't find key from displayName. try refresh template list. or you're using custom dict?")
  
  def get_template_value(self, name: str, rtl_resized:bool=False) -> Tuple[dict, str]:
    try:
      value = self.full()[name]
      if rtl_resized and value:
        return name
    except KeyError as e:
      print(f"Exchange displayName: {name} ->", end="")
      tmp = self.get_key_by_dn(self.full(), name)
      value = self.full()[tmp]
      
      if rtl_resized:
        return tmp
    try:
      _ = value[0]
      if len(value) == 4:
        version = "v1"
      elif value[0] == "v2":
        version = "v2"
      elif value["Method"] == "v3":
        version = "v3"
      else:
        raise ValueError("Could not analyze method version")
    except IndexError as e:
      print(f"Catched: IndexError {e}")
      print("pass..  (generate.py / get_template_value)")
      if len(value) == 4:
        version = "v1"
      elif value["Method"] == "v3":
        version = "v3"
      else:
        raise ValueError("Couldn't analyze method version")
    except KeyError as e:
      print(f"Catched: KeyError {e}")
      print("pass.. (generate.py / get_template_value)")
      version = value["Method"]
    return value, version

class _generate_common:
  obtain_lora_list = obtain_lora_list()
  obtain_template_list = obtain_template_list()
  

class generate_common(Importable):
  def __init__(self):
    return
  def __call__(self, **kwargs):
    return _generate_common