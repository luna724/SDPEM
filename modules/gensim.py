import requests
from gensim.models import KeyedVectors
import os, shutil
import gdown, gzip

import shared


class Gensim:
    def __init__(
            self,
            word2vec_model_name = None
    ):
        if word2vec_model_name is None:
            word2vec_model_name = shared.model_file["word2vec"]
        if word2vec_model_name == "GoogleNews-vectors-negative300.bin":
            if not os.path.exists("GoogleNews-vectors-negative300.bin"):
                print("Gensim (word2vec) model not found. downloading.. ", end="")
                url = 'https://drive.google.com/uc?id=0B7XkCwpI5KDYNlNUTTlSS21pQmM'
                output_gz = 'GoogleNews-vectors-negative300.bin.gz'
                gdown.download(url, output_gz, quiet=False)
                output_bin = 'GoogleNews-vectors-negative300.bin'
                print("done")

                # 解凍処理
                print("Gensim (word2vec) model extracting.. ", end="")
                with gzip.open(output_gz, 'rb') as f_in:
                    with open(output_bin, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out) #ignore: type
                        print("done")

        print("Loading Word2Vec model..", end=" ")
        self.model = KeyedVectors.load_word2vec_format(word2vec_model_name, binary=True)
        print("done")

    def compare_words_word2vec(self, word1, word2, model = None):
        model = model or self.model
        try:
            similarity = model.similarity(word1, word2)
            return similarity
        except KeyError:
            return None  # 単語がボキャブラリにない場合

    def compare_words(
            self,
            word1: str, word2: str, threshold: float = 0.75,
            model: KeyedVectors = None
    ) -> tuple[bool, float]:
        similarity = self.compare_words_word2vec(word1, word2, model)
        if similarity is None:
            print("[ERROR]: Failed to compare words with Word2Vec")
            return (None, None)
        match = similarity >= threshold
        return (match, similarity)
default = Gensim()