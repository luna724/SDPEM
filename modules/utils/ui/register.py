import json
import gradio as gr
import inspect
from pathlib import Path
from modules.preset import PresetManager
from utils import error, warn
from modules.utils.ui.globals import register_instance

rcMap: dict = {} # instance_name: RegisterComponent

class ValuesMap:
  def __init__(self, rc: "RegisterComponent", values: dict, pname: str):
    self.values = values
    self.name = rc.instance_name or type(rc).__name__
    self.name += f" | {pname}"
  
  def __getattr__(self, name):
    try:
      return self.values[name]
    except KeyError:
      warn(f"[{self.name}]: default value isn't set! ({name})")
      return None
  
  def __call__(self, key: str, default=None):
    if key in self.values:
      return self.values[key]
    else:
      warn(f"[{self.name}]: default value isn't set! ({key})")
      return default

class RegisterComponent:
  @staticmethod
  def get_rc(instance_name: str) -> "RegisterComponent":
    if instance_name not in rcMap:
      raise KeyError(f"RegisterComponent instance '{instance_name}' not found.")
    return rcMap[instance_name]
  
  def __init__(self, fp: Path, instance_name: str):
    # self.fp: Path = fp
    if not instance_name or not isinstance(instance_name, str):
      raise ValueError("RegisterComponent requires a non-empty string 'instance_name'.")
    self.instance_name = instance_name
    self.components = {}
    self.ordered_components = {}
    self.pmgr: PresetManager = PresetManager(instance_name.replace("/", "."))
    self.conf: ValuesMap = None
    
    register_instance(self.instance_name, self)
    rcMap[instance_name] = self

  def register(self, key: str, c: gr.components.Component, order: int = None):
    if not isinstance(key, str): raise TypeError(f"Key aren't str: {key}")
    self.components[key] = c
    if not isinstance(order, int):
      order = len(self.ordered_components) + 1

    self.ordered_components[order] = [key, c]
    return c
  
  def to_dict(self, *values) -> dict:
    return dict(
      zip(
        self.components.keys(),
        values
      )
    )
  
  def save_ui(self, pname: str, *values):
    """btn.click(fn=insta_save, inputs=[pname] + [this.values()]) で使用可能"""
    self.pmgr.save(pname, self.to_dict(*values))
    gr.Info(f"Configuration '{pname}' saved.")
    return None
    
  def save(self, values: list, dont_saves: list[str] = [], pname: str = "default"):
    """valuesは this.values() で取得可能"""
    vd = self.to_dict(*values)
    vd = {k: v for k, v in vd.items() if k not in dont_saves}
    
    self.pmgr.save(pname, vd)
    return
  
  def keys(self) -> list:
    return list(self.components.keys())
  
  def values(self) -> list:
    """登録されたコンポーネントの値を取得"""
    return list(self.components.values())
  
  def ordered_keys(self) -> list:
    return [x[0] for x in self.ordered_components.values()]

  def ordered_values(self) -> list:
    return [x[1] for x in self.ordered_components.values()]
  
  def get(self, pname: str = "default") -> ValuesMap:
    pname = pname or self.pmgr.current_preset
    self.conf = ValuesMap(
      self,
      self.pmgr.load(pname),
      pname
    )
    return self.conf

  def __call__(self, key: str, c: gr.components.Component, order: int = None, **kw):
    return self.register(key, c, order, **kw)