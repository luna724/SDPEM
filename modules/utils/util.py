import hashlib
import random

def sha256(data: str | bytes) -> str:
  if isinstance(data, str):
    data = data.encode('utf-8')
  return hashlib.sha256(data).hexdigest()

def safe_rndrange(start: int | float, stop: int | float, step: int | float = 1) -> int | float:
  if start >= stop:
    return start
  if isinstance(start, float) or isinstance(stop, float) or isinstance(step, float):
    decimals = 0
    for val in (start, stop, step):
      if isinstance(val, float):
        s = f"{val:.10f}".rstrip('0')
        if '.' in s:
          decimals = max(decimals, len(s.split('.')[1]))
    factor = 10 ** decimals
    start_int = int(round(start * factor))
    stop_int = int(round(stop * factor))
    step_int = int(round(step * factor)) if isinstance(step, float) or step != 1 else 1
    if step_int <= 0:
      step_int = 1
    if start_int >= stop_int:
      return start
    return random.randrange(start_int, stop_int, step_int) / factor
  return random.randrange(start, stop, step)

def rndrange(arg, stop=None):
  if stop is None:
    if isinstance(arg, (list, tuple)):
      return safe_rndrange(arg[0], arg[1])
    raise TypeError('rndrange requires a sequence of two ints or two int arguments')
  return safe_rndrange(arg, stop)