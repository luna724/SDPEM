import itertools

from transformers import BertTokenizer, BertModel, PreTrainedTokenizerBase, PreTrainedModel
from sentence_transformers import SentenceTransformer, util
import torch
from typing import *

class BERT:
    def __init__(
            self,
            model_name = 'bert-base-uncased',
            tokenizer_name = 'bert-base-uncased',
            sentence_name = 'all-MiniLM-L6-v2'
    ):
        print("Loading BERT model.. ", end="")
        self.model = BertModel.from_pretrained(model_name)
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)
        self.sentence = SentenceTransformer(sentence_name)
        print("done")

    def get_word_embeddings_with_normal_bert(
            self,
            word, tokenizer: PreTrainedTokenizerBase = None,
            model: PreTrainedModel = None
    ) -> tuple:
        """

        :param word: - target word
        :param tokenizer: - Tokenizer if None, use initial tokenizer
        :param model: - Model if None, use initial Model
        :return: - (average_embedding, raw_embeddings)
        """
        tokenizer = tokenizer or self.tokenizer
        model = model or self.model

        inputs = tokenizer(word, return_tensors="pt")
        outputs = model(**inputs)

        embeddings = outputs.last_hidden_state
        # [CLS]と[SEP]トークンを除外し、残りのトークンの平均を計算
        embedding = embeddings[0][1:-1].mean(dim=0)

        return (embedding, embeddings)

    def compare_words(
            self,
            word1: str, word2: str, threshold: float = 0.75,
            compare_mode: Literal["normal"] = "normal",
            tokenizer: PreTrainedTokenizerBase = None,
            model: PreTrainedModel = None
    ) -> tuple[bool, float]:
        """
        :return: (is_similarity, similarity)
        """
        if compare_mode == "normal":
            emb1 = self.get_word_embeddings_with_normal_bert(word1, tokenizer, model)[0]
            emb2 = self.get_word_embeddings_with_normal_bert(word2, tokenizer, model)[0]
        else:
            raise ValueError("Unknown compare mode in BERT:compare_words")

        # コサイン類似度を計算
        cos = torch.nn.CosineSimilarity(dim=0)
        similarity = cos(emb1, emb2).item()
        matched = similarity >= threshold
        return (matched, similarity)

    def compare_multiply_words(
            self,
            words: List[str], threshold: float,
            tokenizer: PreTrainedTokenizerBase = None,
            model: PreTrainedModel = None
    ) -> str:
        """for UI function"""
        strs = ""
        for target_word, compare_word in itertools.combinations(words, 2):
            result = self.compare_words(
                target_word, compare_word, threshold, "normal", tokenizer, model
            )
            strs += f"{target_word} and {compare_word} are "
            match = result[0]
            if match:
                strs += "matched. "
            else:
                strs += "unmatched. "
            strs += f"({result[1]})\n"
        return strs
default = BERT()