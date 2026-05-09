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

def rndrange(i):
  return safe_rndrange(i[0], i[1])