from io import TextIOWrapper
import json
import traceback
from logger import error

def load(f: TextIOWrapper, encoding="utf-8", insert_empty: bool = False) -> list[dict]:
    s = f.read()
    return loads(s, encoding=encoding, insert_empty=insert_empty)

def loads(s: str, encoding="utf-8", insert_empty: bool = False) -> list[dict]:
    r = []
    for i, l in enumerate(s.splitlines()):
        if l.strip() == "": continue
        
        try:
            r.append(json.loads(l, encoding=encoding))
        except json.JSONDecodeError as e:
            error(f"Failed to parse JSONL line {i}")
            traceback.print_exc()
            if insert_empty: r.append({})
            
    return r

def dump(data: list[dict], f: TextIOWrapper, ensure_ascii: bool = False, encoding="utf-8") -> str:
    to_write = dumps(data, ensure_ascii=ensure_ascii, encoding=encoding)
    f.write(to_write)

def dumps(data: list[dict], ensure_ascii: bool = False, encoding="utf-8") -> str:
    to_write = ""
    for entry in data:
        to_write += json.dumps(entry, indent=None, ensure_ascii=ensure_ascii, encoding=encoding) + "\n"
    return to_write 