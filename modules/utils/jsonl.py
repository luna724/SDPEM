from io import TextIOWrapper
import json
import traceback
import os
from logger import error
import zstandard

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

def append(
    data: dict | list[dict],
    fp: str, ensure_ascii: bool = False, encoding="utf-8",
    check_tail_escape: bool = False,
) -> bool:
    if not os.path.exists(fp): return False
    with open(fp, "a", encoding=encoding) as f:
        if check_tail_escape:
            if f.tell() > 0:
                f.seek(-1, 2)
                if f.read(1) != "\n":
                    f.write("\n")
        if isinstance(data, dict):
            f.write(json.dumps(data, indent=None, ensure_ascii=ensure_ascii, encoding=encoding) + "\n")
        elif isinstance(data, list):
            for entry in data:
                f.write(json.dumps(entry, indent=None, ensure_ascii=ensure_ascii, encoding=encoding) + "\n")
    return True
class zstd:
    @staticmethod
    def load(f, encoding="utf-8", insert_empty: bool = False) -> list[dict]:
        """zstd圧縮されたJSONLファイルを読み込む"""
        compressed_data = f.read()
        return loads(compressed_data, encoding=encoding, insert_empty=insert_empty)

    @staticmethod
    def loads(data: bytes | str, encoding="utf-8", insert_empty: bool = False) -> list[dict]:
        """zstd圧縮されたJSONL文字列をデコードして読み込む"""
        if isinstance(data, str):
            data = data.encode(encoding)
        
        dctx = zstandard.ZstdDecompressor()
        decompressed = dctx.decompress(data)
        s = decompressed.decode(encoding)
                
        return loads(s, encoding=encoding, insert_empty=insert_empty)

    @staticmethod
    def dump(data: list[dict], f, ensure_ascii: bool = False, encoding="utf-8", level: int = 3) -> None:
        """データをzstd圧縮してファイルに書き込む"""
        compressed = dumps(data, ensure_ascii=ensure_ascii, encoding=encoding, level=level)
        f.write(compressed)

    @staticmethod
    def dumps(data: list[dict], ensure_ascii: bool = False, encoding="utf-8", level: int = 3) -> bytes:
        """データをzstd圧縮して返す"""
        to_write = dumps(data, ensure_ascii=ensure_ascii, encoding=encoding)
        
        cctx = zstandard.ZstdCompressor(level=level)
        compressed = cctx.compress(to_write.encode(encoding))
        return compressed