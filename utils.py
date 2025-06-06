import datetime
import os
from typing import Any, Dict
import pyjson5

class AnsiColors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

def now() -> str:
  return datetime.datetime.now().strftime("%H:%M:%S")

def println(*args: Any, **kw: Any) -> None:
  print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.GREEN}INFO{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def printerr(*args: Any, **kw: Any) -> None:
  print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.RED}ERROR{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def printwarn(*args: Any, **kw: Any) -> None:
  print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.YELLOW}WARN{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)

def print_critical(*args: Any, **kw: Any) -> None:
  print(f"{AnsiColors.GRAY}[{now()}] {AnsiColors.BOLD}{AnsiColors.RED}CRITICAL!{AnsiColors.RESET} {' '.join(map(str, args))}", **kw)


def update_enviroments(path: str = "enviroments.json5") -> Dict[str, Any]:
  """Load environment variables from a JSON5 file and update os.environ."""
  if not os.path.exists(path):
    print_critical(f"Environment file {path} not found.")
    raise FileNotFoundError(f"Environment file {path} not found.")
  try:
    with open(path, "r", encoding="utf-8") as f:
      data: Dict[str, Any] = pyjson5.load(f)
    for k, v in data.items():
      os.environ[k] = str(v)
    return data
  except Exception as e:
    print_critical(f"Failed to load environments: {e}")
    raise
