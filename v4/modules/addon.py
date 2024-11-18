from typing import *
from v4.lunapy_module_importer import Importer, Importable
from v4.LGS import jsoncfg
import os

collectorTypes = Importer("modules.types", isTypes="collector")
class _addon(collectorTypes):
  def detect_all_addons(self):
    self.all_addons = [
      os.path.join(self.addon_root, addon)
      for addon in os.listdir(self.addon_root)
    ]
    return self.all_addons
  
  def preload(self, addon):
    """preload 読み込みデータを梱包する"""
    addon_name = os.path.relpath(addon, self.addon_root)
    if not os.path.exists(addon): return "ERR: addon not found"
    
    hasMetadata = False
    initializer = "init.py"
    
    # metadata.json の読み込み
    if os.path.exists(os.path.join(addon, "metadata.json")):
      metadata = jsoncfg.read(os.path.join(addon, "metadata.json"))
      initializer = metadata["init"]
      hasMetadata = True
    
    if not initializer.lower().endswith(".py"): initializer += ".py"
    if not os.path.exists(os.path.join(addon, initializer)):
      print(f"[Addon Loader]: [{addon_name}]: [Critical] couldn't found initializer")
      return "ERR: Addon init not found"
    return (hasMetadata, initializer)
    
  def preload_all(self):
    # Initialize
    self.detect_all_addons()
    
    addons = self.all_addons
    
    addons_data = []
    for addon in addons:
      item = self.preload(addon)
      if isinstance(item, str) and item.startswith("ERR: "): continue
      
      addons_data.append(
        item
      )
    self.addons = addons_data
  
  def load(self, data):
    """data: Preload data"""
    return
  
  def load_specify_addon(self, addon_name: str | tuple):
    if isinstance(addon_name, (tuple, list)):
      self.load(addon_name)
    else:
      pre = self.preload(addon_name)
      if isinstance(pre, str):
        print(f"[Addon Loader]: [{addon_name}]: {pre}")
        return
      self.load(pre)
    
  def load_addons(self):
    """Load ALL Addons"""
    return
  
  def __init__(self):
    super().__init__()  
    self.root = self.config.get_root_path()
    self.addon_root = os.path.join(self.root, "addons")
    
    self.all_addons = self.detect_all_addons()

class addon(Importable):
  def __call__(self, **kw):
    return _addon()