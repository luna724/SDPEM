import json
from utils import println
from pathlib import Path



proot = Path("config/presets")
pf = proot / "pmgr.json"
class PresetManager:
  @staticmethod
  def read_pmgr() -> dict:
    if not pf.exists():
      with pf.open("w", encoding="utf-8") as f:
        json.dump({}, f, indent=2, ensure_ascii=False)
      
    with pf.open("r", encoding="utf-8") as f:
      return json.load(f)
  
  def update_current_preset(self, pname: str):
    pmgr = self.read_pmgr()
    pmgr[self.name] = pname
    with pf.open("w", encoding="utf-8") as f:
      json.dump(pmgr, f, indent=2, ensure_ascii=False)
  
  @property
  def current_preset(self) -> str:
    d = self.read_pmgr().get(self.name, "default")
    return d if d in self.list_presets() else "default"
  
  def __init__(self, mname: str):
    self.name = mname
    self.path = proot / mname
    self.path.mkdir(parents=True, exist_ok=True)
    self.vpreset_dir = {}
  
  def load(self, pname: str) -> dict:
    if pname in self.vpreset_dir:
      self.update_current_preset(pname)
      return self.vpreset_dir[pname]
    
    ppath = self.path / f"{pname}.json"
    if not ppath.exists():
      if pname == "default":
        self.save("default", {})
        println(f"Default preset created for module '{self.name}'.")
        return {}
      raise FileNotFoundError(f"Preset '{pname}' does not exist in module '{self.name}'.")
      
    with open(ppath, "r", encoding="utf-8") as f:
      data = json.load(f)
    self.update_current_preset(pname)
    return data

  def save(self, pname: str, data: dict = None) -> None:
    if pname in self.vpreset_dir:
      self.vpreset_dir.pop(pname)
    
    ppath = self.path / f"{pname}.json"
    with open(ppath, "w", encoding="utf-8") as f:
      json.dump(data, f, indent=2, ensure_ascii=False)
    println(f"Preset '{pname}' saved successfully in module '{self.name}'.")
    self.update_current_preset(pname)
  
  def save_ram(self, pname: str, data: dict = None) -> None:
    self.vpreset_dir[pname] = data
    println(f"Preset '{pname}' saved in RAM for module '{self.name}'.")
    self.update_current_preset(pname)
  
  def list_presets(self) -> list[str]:
    return list(self.vpreset_dir.keys()) + [f.stem for f in self.path.glob("*.json")] 