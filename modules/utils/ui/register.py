import json
import gradio as gr
import inspect
from pathlib import Path
from utils import printerr

class ValuesMap:
  def __init__(self, rc: "RegisterComponent", values: dict):
    self.values = values
    self.name = rc.instance_name or type(rc).__name__
  
  def __getattr__(self, name):
    try:
      return self.values[name]
    except KeyError:
      printerr(f"[{self.name}]: default value isn't set! ({name})")
      return None

class RegisterComponent:
  def __init__(self, fp: Path, instance_name: str = None):
    self.fp: Path = fp
    self.instance_name = instance_name or self._get_variable_name()
    self.components = {}
    self.ordered_components = {}
    self.loaded_conf: dict = {}
    if not self.fp.exists():
      self.fp.parent.mkdir(parents=True, exist_ok=True)
      self.conf = ValuesMap(self, {})
    else:
      self.conf = self.load()

  def _get_variable_name(self):
    """呼び出し元のフレームから変数名を取得する試み"""
    try:
      frame = inspect.currentframe().f_back.f_back
      for name, obj in frame.f_locals.items():
        if obj is self:
          return name
      # ローカル変数で見つからない場合はグローバル変数を確認
      for name, obj in frame.f_globals.items():
        if obj is self:
          return name
    except:
      pass
    return "RegisterComponent"

  def register(self, key: str, c: gr.components.Component, order: int = None):
    if not isinstance(key, str): raise TypeError(f"Key aren't str: {key}")
    self.components[key] = c
    if not isinstance(order, int):
      order = len(self.ordered_components) + 1

    self.ordered_components[order] = [key, c]
    return c
  
  def save(self, values):
    """valuesは this.values() で取得可能"""
    values = dict(
      zip(
        self.components.keys(),
        values
      )
    )
    with self.fp.open("w", encoding="utf-8") as f:
      json.dump(values, f, ensure_ascii=False, indent=2)
    self.loaded_conf = values
    self.conf = ValuesMap(self, values)
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

  def load(self) -> ValuesMap:
    if not self.fp.exists():
      raise FileNotFoundError(f"Configuration file {self.fp} does not exist.")
    
    with self.fp.open("r", encoding="utf-8") as f:
      values = json.load(f)
    self.loaded_conf = values
    return ValuesMap(
      self,
      self.loaded_conf
    )
  
  def get(self) -> ValuesMap:
    return self.conf