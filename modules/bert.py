import itertools

from transformers import BertTokenizer, BertModel, PreTrainedTokenizerBase, PreTrainedModel
from sentence_transformers import SentenceTransformer, util
import torch
from typing import *

import shared
from modules.model_loader import ModelLoaderClassUtil


class BERT(ModelLoaderClassUtil):
    def __init__(
            self,
            model_name = None,
            tokenizer_name = None,
            sentence_name = None
    ):
        super().__init__("BERT")
        load_state = not (shared.args.no_bert or shared.args.nolm)
        if load_state:
            if model_name is None:
                model_name = shared.model_file["bert_model"]
            if tokenizer_name is None:
                tokenizer_name = shared.model_file["bert_tokenizer"]
            if sentence_name is None:
                sentence_name = shared.model_file["sentence_name"]

            print("[BERT]: Loading BERT model.. ", end="")
            self.model = BertModel.from_pretrained(model_name)
            self.tokenizer = BertTokenizer.from_pretrained(tokenizer_name)
            self._sentence = SentenceTransformer(sentence_name)
            print("done")

            self._send_model_to_cpu()
        else:
            print("[BERT]: Specify Arguments accepted. BERT disabled.")

    def __get_word_embeddings_with_normal_bert(
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

        return embedding, embeddings

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
        model_state = self.model_null_safe(model)
        if not model_state:
            return False, 0

        self._send_model_to_cuda()
        if compare_mode == "normal":
            emb1 = self.__get_word_embeddings_with_normal_bert(word1, tokenizer, model)[0]
            emb2 = self.__get_word_embeddings_with_normal_bert(word2, tokenizer, model)[0]
        else:
            raise ValueError("Unknown compare mode in BERT:compare_words")

        # コサイン類似度を計算
        cos = torch.nn.CosineSimilarity(dim=0)
        similarity = cos(emb1, emb2).item()
        matched = similarity >= threshold
        return matched, similarity

    def compare_multiply_words(
            self,
            words: List[str], threshold: float,
            tokenizer: PreTrainedTokenizerBase = None,
            model: PreTrainedModel = None
    ) -> str:
        """for UI function"""
        strs = ""
        if not self.model_null_safe(model):
            return "--noLM or --noBERT arguments given.\nthis features was disabled."

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