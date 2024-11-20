import hashlib
import re
from datetime import datetime
from typing import *

class Util:
    """現在時刻を isoformat で返す"""
    @staticmethod
    def time_now() -> str:
        return datetime.now().isoformat()

    """ コンマで区切り、対象パターンのindex0のすべてを持つリストを返す"""
    @staticmethod
    def re4prompt_v4(pattern: str, text: str) -> List[str]:
        prompt_piece = text.split(",")
        rtl = []

        for x in prompt_piece:
            x = x.strip()
            r = re.findall(pattern, x)
            if r:
                rtl.append(r[0])

        return rtl

    """sha256を計算"""
    @staticmethod
    def calculate_sha256(obj: Any) -> str:
        hash_obj = hashlib.sha256()
        hash_obj.update(obj)
        return hash_obj.hexdigest()