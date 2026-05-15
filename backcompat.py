import os
import shutil
from pathlib import Path

VERSION = 2

def backcompat():
  try:
    with open("config/backcompat", "r") as f:
      bc_version = int(f.read().strip())
  except FileNotFoundError:
    bc_version = 0
  except TypeError:
    bc_version = VERSION + 1
    print("Invalid backcompat version format. Please ensure 'config/backcompat' contains a valid integer.")

  if VERSION == bc_version:
    return
  elif VERSION < bc_version:
    print(f"Detected newer backcompat version {bc_version}. Please update sdpem.")
    return
  
  # version 1
  # defaults/*の削除、config/presets/への以降
  if bc_version < 1:
    for d in os.listdir("defaults"):
      if not d.endswith("json"):
        continue
      name = d[:-5]
      src = os.path.join("defaults", d)
      dst_dir = Path(os.path.join("config", "presets", name, "default.json"))
      dst_dir.parent.mkdir(parents=True, exist_ok=True)
      os.rename(src, os.path.abspath(str(dst_dir)))
      # os.remove(src)
    shutil.rmtree("defaults")
    bc_version = 1
    
  # version 2
  # forever_generation/common の統合
  if bc_version < 2:
    from modules.backcompat._2 import bc
    if bc():
      bc_version = 2
  
  if bc_version < 3:
    from modules.backcompat._2 import bc_3
    if bc_3():
      bc_version = 3
  
  with open("config/backcompat", "w") as f:
    f.write(str(bc_version))