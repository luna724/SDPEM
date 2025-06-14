import hashlib

def sha256(data: str | bytes) -> str:
  if isinstance(data, str):
    data = data.encode('utf-8')
  return hashlib.sha256(data).hexdigest()