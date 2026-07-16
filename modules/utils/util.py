import hashlib
import random

def sha256(data: str | bytes) -> str:
  if isinstance(data, str):
    data = data.encode('utf-8')
  return hashlib.sha256(data).hexdigest()

def safe_rndrange(start: int, stop: int, step: int = 1) -> int:
  if start >= stop:
    return start
  return random.randrange(start, stop, step)

def rndrange(arg, stop=None):
  if stop is None:
    if isinstance(arg, (list, tuple)):
      return safe_rndrange(arg[0], arg[1])
    raise TypeError('rndrange requires a sequence of two ints or two int arguments')
  return safe_rndrange(arg, stop)