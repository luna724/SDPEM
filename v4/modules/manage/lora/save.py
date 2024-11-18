from v4.lunapy_module_importer import Importable, Importer
from typing import *
from v4.LGS import jsoncfg
import gradio as gr
import os

generatorTypes = Importer("modules.types", isTypes="generator")
class _save(generatorTypes):
  @staticmethod
  def getBase():
    lora_base = [
      "v5", {
        "lora": "<lora:example:1.0>",
        "name": "NAME",
        "prompt": "PROMPT",
        "extend": "EXTEND",
        "key": "",
        "lora_variables": [
          [False, False],
          [["Var1", "info1"], ["Var2", "info2"]]
        ],
        "loraisLoRA": True
      }
    ]
    return lora_base
  
  def genBase(self, lora:str, name:str, prompt:str, extend:str, key:str, lv1:bool, lv1s:List[str], lv2:bool, lv2s:List[str], loraisid:bool|None, **kw):
    base = self.getBase()
    basic = {
      "lora": lora,
      "name": name,
      "prompt": prompt,
      "extend": extend,
      "key": key,
      "lora_variables": [
        [lv1, lv2],
        [lv1s, lv2s]
      ],
      "loraisLoRA": loraisid
    }
    base[1].update(basic)
    return base
  
  def __init__(self):
    super().__init__()
    self.get_lora = self.generate_common.obtain_lora_list
    self.avv = ["v5"]
    self.recommend_version = 0 # INDEX
  
  def get_avv(self):
    return self.avv
  
  def get_recommend_version(self):
    return self.avv[self.recommend_version]
  
  def check_lora_id(self, lora_id:str, isID:str) -> bool:
    """return: bool(isID)"""
    if isID == "Yes":
      isID = True
    elif isID == "No":
      isID = False
    else:
      isID = None
    
    lora_id = lora_id.strip()
    
    if isID is None:
      # Auto-detect
      if "<lora:" in lora_id.lower():
        isID = True
      else:
        isID = False
    
    if lora_id == "." or not isID:
      return isID
    
    try:
      self.lib.control_lora_weight(lora_id)
    except IndexError:
      gr.Warning("LoRA ID hasn't correctly!")
      return isID
    gr.Info("No errors occurred")
    return isID
  
  def bool2visible(self, boo):
    return self.lib.bool2visible(boo)
  
  def load_primary(self,
    target, displayName, lora_id, lora_id_is_lora, name, prompt, extend,
    lv1, lv1_title, lv1_prompt, lv2, lv2_title, lv2_prompt, overwrite
  ):
    if not displayName == "":
      entered_data = {
        displayName: self.genBase(
          lora_id, name, prompt, extend, displayName,
          lv1, [lv1_title, lv1_prompt], lv2, [lv2_title, lv2_prompt], lora_id_is_lora
        )
      }
      print("[Load]: entered data found. printing drafts..")
      print("Entered: ", entered_data)
    lora = self.get_lora.full()
    if not target in list(lora.keys()):
      raise gr.Error("Can't find LoRA Template.")

    data = lora[target][1]
    ver = lora[target][0]
    print("[Load]: Template version: ", ver)
    if ver in ["v4", "v5"]:
      # v4 return
      ret = ["Success!", target, data["lora"], data["name"], data["prompt"], data["extend"]]
      if ver == "v5":
        lv = data["lora_variables"]
        lil = data["loraisLoRA"]
        if lil is None:
          lil = "auto"
        elif lil:
          lil = "Yes"
        else:
          lil = "No"
          
        ret += [lv[0][0], lv[1][0][0], lv[1][0][1], lv[1][1], lv[1][1][0], lv[1][1][1], lil]
      else:
        ret += [False, "", "", False, "", "", True]
      return ret+[True]
    else:
      raise gr.Error(f"{ver} isn't supported on V5-Load")
  
  def save_primary(self,
    target, displayName, lora_id, lora_id_is_lora, name, prompt, extend,
    lv1, lv1_title, lv1_prompt, lv2, lv2_title, lv2_prompt, overwrite
  ):
    if displayName == "" or displayName == None:
      raise gr.Error("Please enter displayName!")
    
    if lora_id_is_lora == "Yes":
      lora_id_is_lora = True
    elif lora_id_is_lora == "No":
      lora_id_is_lora = False
    else:
      lora_id_is_lora = None
    
    if lora_id_is_lora is not None and lora_id_is_lora:
      try:
        lora_id_is_lora = self.check_lora_id(lora_id, True)
      except Exception:
        lora_id_is_lora = True
        pass
    
    if lora_id == ".":
      lora_id = ""
    
    lv1s = [lv1_title, lv1_prompt]
    lv2s = [lv2_title, lv2_prompt]
    data = {"lora":lora_id, "name": name, "prompt": prompt, "extend": extend, "key":displayName,
            "lv1": lv1, "lv1s": lv1s, "lv2": lv2, "lv2s": lv2s, "loraisid": lora_id_is_lora}
    date = self.genBase(**data)
    
    db = {
      displayName: date
    }
    all_db = self.get_lora.full()
    
    passed = False
    if displayName in list(all_db.keys()):
      print("[Save]: displayName duplication found.")
    else:
      passed = True
    
    if not overwrite and not passed: # passed = False ということは duplication があるということ
      print("[Save]: catch Exception (keys already found)")
      raise gr.Error("this displayNames already taken.")
    
    if overwrite and not passed:
      print("[Save]: printing previous data..")
      print("[Save]: [prv_data]: ", all_db[displayName])
      gr.Info("previous data found! (overwrite=True)")
      
    all_db.update(db)
    jsoncfg.write(
      all_db, os.path.join(self.config.get_data_path(), "lora_template.json")
    )
    
    
class save(Importable):
  def __init__(self):
    return
  def __call__(self, **kw):
    return _save()