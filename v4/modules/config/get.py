from v4.lunapy_module_importer import Importable
from pydantic import BaseModel
from typing import *
from v4.LGS import jsoncfg
import os

class config_value(BaseModel):
  database_ui:dict
  script_version:dict
  user_variable:dict
  system:dict

class _get:
  def get_root_path(self) -> str:
    """return script root_path.
    if PEM, return ROOT_DIR
    if PDB, return Extensions ROOT_DIR
    """
    return self.rootdir
  
  def get_data_path(self) -> str:
    """return config's root_path"""
    return self.path
  
  def update_config(self) -> None:
    """update config values"""
    raw = jsoncfg.read(
      os.path.join(self.get_data_path(), "main_config.json")
    )
    self.config_values = config_value(**raw)
  
  def get_spec_value(self, locate:str) -> Any:
    if locate.count(".") >= 1:
      p1 = locate.split(".")[0]
    else:
      p1 = locate
    
    if hasattr(self.config_values, p1):
      value = getattr(self.config_values, p1)
      
      if isinstance(value, dict):
        for x in locate.split(".")[1:]:
          if x in value.keys():
            value = value[x]
          else:
            raise ValueError(f"Cannot find key '{x}' in the config path '{locate}'")
      else:
        raise ValueError(f"Config path '{locate}' does not point to a dictionary")
    else:
      raise ValueError(f"Cannot find top-level key '{p1}' in the config path '{locate}'")

    return value
  
  def get_spec_values(self, locates:List[str]) -> List[Any]:
    return [
      self.get_spec_value(item)
      for item in locates 
      if isinstance(item, str)
    ] 
  
  def __init__(self, isPEM:bool):
    self.isPEM = isPEM
    if isPEM:
      self.rootdir = os.getcwd()
      self.path = os.path.join(self.rootdir, "configs")
    else:
      from luna_py import rootdir
      from lunapy.sdpdb.database_root import DB_PATH
      self.rootdir = rootdir
      self.path = DB_PATH
    
    self.update_config()
    pass
  
  
class get_main(Importable):
  def __init__(self):
    return
  def __call__(self, **kwargs):
    return _get(kwargs["isPEM"])