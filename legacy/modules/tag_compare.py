import itertools
from typing import *

from modules.models.fast_text import default as fasttext
from modules.models.gensim import default as gensim
from modules.util import Util

class TagCompareUtilities(Util):
    def __init__(self):
        pass

    @staticmethod
    def compare_is_in(
            word1: str, word2: str, threshold: float = 0.75
    ) -> tuple[bool, float]:
        is_matched, similarity = gensim.compare_words(word1, word2, threshold)
        if is_matched is None:
            is_matched, similarity = fasttext.compare_words(word1, word2, threshold)
        return is_matched, similarity

    def check_typo_multiply(
            self,
            target: str, typos: List[str], threshold: float = 0.75
    ):
        return any(
            self.compare_is_in(target, typo, threshold)[0] for typo in typos
        )

    def compare_multiply_words_for_ui(
            self,
            words: List[str], threshold: float
    ) -> str:
        """for UI function"""
        strs = ""
        for target_word, compare_word in itertools.combinations(words, 2):
            result = self.compare_is_in(
                target_word, compare_word, threshold
            )
            strs += f"{target_word} and {compare_word} are "
            match = result[0]
            if match:
                strs += "matched. "
            else:
                strs += "unmatched. "
            strs += f"({result[1]})\n"
        return strs