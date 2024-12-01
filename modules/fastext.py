import fasttext
import fasttext.util
import os
from numpy import dot
from numpy.linalg import norm

import shared


class FastText:
    def __init__(
            self,
            pretrained_model: str = None
    ):
        if pretrained_model is None:
            pretrained_model = shared.model_file["fasttext"]
        if pretrained_model == "cc.en.300.bin":
            if not os.path.exists("cc.en.300.bin"):
                print("model not exists. downloading FastText 300dim-EN..", end="")
                fasttext.util.download_model('en', if_exists='ignore')
                print(" done")
        elif pretrained_model == "cc.en.100.bin":
            if not os.path.exists("cc.en.100.bin"):
                print("model not exists. reducing FastText 100dim-EN..", end="")
                if not os.path.exists("cc.en.300.bin"):
                    print("model not exists. downloading FastText 300dim-EN..", end="")
                    fasttext.util.download_model("en", if_exists="ignore")
                    print(" done")

                dim300 = fasttext.load_model("cc.en.300.bin")
                dim100 = fasttext.util.reduce_model(dim300, 100)
                dim100.save_model("cc.en.100.bin")
                print(" done")
                self.model = dim100
                return
        print("loading FastText models.. ", end="")
        self.model = fasttext.load_model(pretrained_model)
        print("done")

    @staticmethod
    def cosine_similarity(vec1, vec2):
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

    def compare_words(
            self,
            word1: str, word2: str, threshold: float = 0.75,
            model = None
    ) -> tuple[bool, float]:
        model = model or self.model
        emb1 = model.get_word_vector(word1)
        emb2 = model.get_word_vector(word2)
        similarity = self.cosine_similarity(emb1, emb2)
        matched = similarity >= threshold
        return matched, similarity

default = FastText()