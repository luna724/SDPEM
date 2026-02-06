import zstandard as zstd


def unzip(data: bytes, encoding="utf-8") -> str:
    """zstd圧縮されたバイト列を展開する"""
    dctx = zstd.ZstdDecompressor()
    decompressed = dctx.decompress(data)
    return decompressed.decode(encoding)

def zip(data: str | bytes, encoding="utf-8", level: int = 3) -> bytes:
    """データをzstd圧縮して返す"""
    if isinstance(data, str):
        data = data.encode(encoding)
    
    cctx = zstd.ZstdCompressor(level=level)
    return cctx.compress(data)
