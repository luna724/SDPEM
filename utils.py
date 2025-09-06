import datetime
import os
from typing import Any, Dict
import pyjson5
from logger import *

def update_enviroments(path: str = "enviroments.json5") -> Dict[str, Any]:
  """Load environment variables from a JSON5 file and update os.environ."""
  if not os.path.exists(path):
    critical(f"Environment file {path} not found.")
    raise FileNotFoundError(f"Environment file {path} not found.")
  try:
    with open(path, "r", encoding="utf-8") as f:
      data: Dict[str, Any] = pyjson5.load(f)
    for k, v in data.items():
      os.environ[k] = str(v)
    return data
  except Exception as e:
    critical(f"Failed to load environments: {e}")
    raise
