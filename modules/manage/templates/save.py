from lunapy_module_importer import Importer, Importable
import gradio as gr
from LGS import jsoncfg
import os

generatorTypes = Importer("modules.types", isTypes="generator")
class save(generatorTypes):
  @staticmethod
  def getBase() -> dict:
    base = {
      "Method": "v4.0.0",
      "Method_Release": 10,
      "displayName": "",
      "Key": "",
      "Values": {
        "Prompt": "",
        "Negative": "",
        "AD_Prompt": "",
        "AD_Negative": "",
        "NSFW_Prompt": ""
      },
      "Hires": {
          "isEnabled": True,
          "Upscale": 1.5,
          "Sampler": "R-ESRGAN 4x+ Anime6B",
          "Denoising": 0.35,
          "Steps": 6
        },
      "Example": {
        "lora": "",
        "weight": 0.75,
        "extend": False,
        "face": ["", ""],
        "location": ["", ""],
        "Headers": ["", ""],
        "Other": ["", ""],
        "clip": 0,
        "image": ""
      },
      "Buildins": {
        "model": "",
        "vae": "Automatic",
        "sampler": "",
        "method": "",
        "refiner": ["", 0.0]
      },
      "ControlNet": {
        "isEnabled": False,
        "Mode": "",
        "Weight": 0.0,
        "Image": ""
      },
      "ADetailer": {
        "1st": {
          "isEnabled": False,
          "model": ""
        }
      }
    }
    return base
  
  def genBase(self, k, p, ng, ads, adm, adp, adng):
    # v4.0-pre1
    base = self.getBase()
    basic = {
      "displayName": k,
      "Key": k,
      "Values": {
        "Prompt": p,
        "Negative": ng,
        "AD_Prompt": adp,
        "AD_Negative": adng,
        "NSFW_Prompt": ""
      },
      "ADetailer": {
        "1st": {
          "isEnabled": ads,
          "model": adm
        }
      }
    }
    base.update(basic)
    return base
  
  def __init__(self):
    super().__init__()
    self.get_templates = self.generate_common.obtain_template_list
    self.get_lora = self.generate_common.obtain_lora_list
    self.model_db = Importer("modules.model_db")
    self.db_norm_values = self.config.get_spec_value("database_ui")
  
    # Variable for UI
    self.available_versions:list = ["v4.0"]
    self.avv_information:dict = {
      # AVV: ["gr.Info caller", save_method_function]
      "v4.0": ["[v4.0]: Compatibility UI version: (v4.1.1R ~ v4.1.1R)", None],
      "v3.0.3": ["[v3.0.3]: Compatibility UI version: V3", None],
      "βv4.1": ["[β4.1]: Compatibility UI version: (None)", None]
    }
  
  # change method
  def activate_method(self, activater):
    """return: (activate.change, disable.change, accordion.change)"""
    if activater:
      return (
        gr.Checkbox.update(visible=False, value=False),
        gr. Checkbox.update(visible=True, value=False),
        gr.update(visible=True)
      )
  
  def deactivate_method(self, deactivater):
    """return: (activate.change, disable.change, accordion.change)"""
    if deactivater:
      return (
        gr.Checkbox.update(visible=True, value=False),
        gr.Checkbox.update(visible=False,value=False),
        gr.update(visible=False)
      )
  
  def selected_version_changer(self, current):
    try:
      info = self.avv_information[current]
      if info[1] is None:
        raise KeyError()
    except KeyError:
      raise gr.Error("version data wasn't found.\n[ErrID:SAVE-000]: this error is NOT throwable")
    desc = info[0]
    self.save = info[1]
    
    if desc is None or desc == "":
      raise gr.Error("version info wasn't found.\n[ErrID:SAVE-001]: Throwable")
    gr.Info(desc)
  
  def bool2visible(self, b, v):
    if b:
      values = f"Deactivate {v}"
    else:
      values = f"Activate {v}"
    return self.lib.bool2visible(b), gr.update(label=values)
  
  def save_primary(self,
    displayName, prompt, negative, ad_status, ad_model, ad_prompt, ad_negative,
    overwrite
    
  ):
    # 変数のチェック
    if displayName in self.lib.empty_variant or displayName == None:
      raise gr.Error("Please enter displayName!")
    
    if negative in self.lib.empty_variant and not negative == ".":
      negative = self.db_norm_values["negative"]
    
    if ad_negative in self.lib.empty_variant and not ad_negative == ".":
      ad_negative = self.db_norm_values["ad_neg"]
    
    data = self.genBase(
      displayName,
      prompt, negative, ad_status, ad_model, ad_prompt, ad_negative
    )
    db = {
      displayName: data
    }
    all_db = self.get_templates.full()
    
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
      all_db, os.path.join(self.config.get_data_path(), "templates.json")
    )
    gr.Info("Success!")
    
class _save(Importable):
  def __call__(self, **kwargs):
    return save()