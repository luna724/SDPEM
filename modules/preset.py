import json
from utils import println
from pathlib import Path

proot = Path("config/presets")
class PresetManager:
  def __init__(self, mname: str):
    self.name = mname
    self.path = proot / mname
    self.path.mkdir(parents=True, exist_ok=True)
  
  def load(self, pname: str) -> dict:
    ppath = self.path / f"{pname}.json"
    if not ppath.exists():
      raise FileNotFoundError(f"Preset '{pname}' does not exist in module '{self.name}'.")
      
    with open(ppath, "r") as f:
      data = json.load(f)
    return data

  def save(self, pname: str, data: dict = None) -> None:
    ppath = self.path / f"{pname}.json"
    with open(ppath, "w") as f:
      json.dump(data, f, indent=2, ensure_ascii=False)
    println(f"Preset '{pname}' saved successfully in module '{self.name}'.")
  
  def list_presets(self) -> list[str]:
    return [f.stem for f in self.path.glob("*.json")]