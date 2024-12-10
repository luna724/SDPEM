import hashlib
import re
from datetime import datetime
from typing import *


class Util:
    @staticmethod
    def time_now() -> str:
        """現在時刻を isoformat で返す"""
        return datetime.now().isoformat()

    @staticmethod
    def re4prompt_v4(pattern: str, text: str) -> List[str]:
        """ コンマで区切り、対象パターンのindex0のすべてを持つリストを返す"""
        prompt_piece = text.split(",")
        rtl = []

        for x in prompt_piece:
            x = x.strip()
            r = re.findall(pattern, x)
            if r:
                rtl.append(r[0])

        return rtl

    @staticmethod
    def calculate_sha256(obj: Any) -> str:
        """sha256を計算"""
        hash_obj = hashlib.sha256()
        hash_obj.update(obj.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    def resize_is_in(base: Iterable, resize_target: Iterable, ignoreCase: bool = False) -> Sequence[str]:
        """resize_targetの値がbaseに含まれるかをチェックし、 ## TODO: ignoreCase の追加
        含まれなかった値を削除した物を返す"""
        return [
            rt
            for rt in resize_target
            if rt in base
        ]

    @staticmethod
    def isbool(x: Any) -> bool:
        if isinstance(x, bool): return True
        else: return False