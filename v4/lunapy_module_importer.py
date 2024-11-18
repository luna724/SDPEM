from typing import *
from types import ModuleType
from abc import abstractmethod
import importlib

class Importable:
  """
  クラスがmoduleImporterからインポートできることを明記するクラス \n
  インポート可能な形式にさせるには 
  Importable のサブクラスとして定義する必要がある
  
  インポート可能なクラスは以下の型を持つ必要がある
  - Importable のサブクラスである
  - __call__ 関数がメインクラスのインスタンス (一般的には 渡されたisPEMに応じた値でイニシャライズされたクラスのインスタンス) のみを返す
  - __init__, __call__ 関数は必須引数を持っていない (__call__ に関しては isPEMを受け付けることも可能。ただし一般的には **kwargs の使用を推奨している)
  
  また、1ファイルに多数のImportableのサブクラスがある場合、
  kwargs内の index_value の値のインデックスを取得する。
  この機能はIndexErrorに対する処理は持っていない。
  
  kwargs内に index_value がない場合は、index0 を返す
  """
  @abstractmethod
  def __call__(self):
    raise ValueError("class: Importable isn't callable. / Initializable.")
  

class moduleImporter:
  def __init__(self, env:Literal["pem", "pdb"]):
    self.env = env == "pem"
    
    if self.env:
      self.path = ""
    else:
      self.path = "repositories.lunapy_sdpem."
  
  def __call__(self, module_path:str, return_moduleType:bool=False, **kwargs) -> Any | ModuleType:
    """from . import . aren't supported.
    returns that module's class.
    
    if return_moduleType, return moduleType"""
    module = importlib.import_module(
      f"{self.path}{module_path}"
    )
    print("[Importer]: called module: ", f"{self.path}{module_path}")
    
    if return_moduleType: return module
    
    mod = []
    for x in module.__dict__.values():
      if isinstance(x, type) and issubclass(x, Importable) and not x == Importable:
        mod.append(x)
    
    if len(mod) == 0:
      raise ImportError(f"Failed to import custom module from {module_path}")
    
    elif len(mod) != 1:
      if "index_value" in kwargs.keys():
        n = kwargs["index_value"]
      
      else:
        n = 0
        
      if "isTypes" in kwargs.keys():
        typess = kwargs["isTypes"]
        typelist = {
          "generator": 0,
          "collector": 1
        }
        n = typelist[typess]
      
      module = mod[n]
    
    else:
      module = mod[0]
    
    return module()(isPEM=self.env)

Importer:moduleImporter = None