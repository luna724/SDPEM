import requests
from gensim.models import KeyedVectors
import os, shutil
import gdown, gzip

import shared
from modules.model_loader import ModelLoaderClassUtil


class Gensim(ModelLoaderClassUtil):
    def __init__(
            self,
            word2vec_model_name = None
    ):
        super().__init__("Gensim")
        load_state = not (shared.args.no_gensim or shared.args.nolm)
        if load_state:
            if word2vec_model_name is None:
                word2vec_model_name = shared.model_file["word2vec"]
            if word2vec_model_name == "GoogleNews-vectors-negative300.bin":
                if not os.path.exists("GoogleNews-vectors-negative300.bin"):
                    print("[Gensim]: Gensim (word2vec) model not found. downloading.. ", end="")
                    url = 'https://drive.google.com/uc?id=0B7XkCwpI5KDYNlNUTTlSS21pQmM'
                    output_gz = 'GoogleNews-vectors-negative300.bin.gz'
                    gdown.download(url, output_gz, quiet=False)
                    output_bin = 'GoogleNews-vectors-negative300.bin'
                    print("done")

                    # 解凍処理
                    print("[Gensim]: Gensim (word2vec) model extracting.. ", end="")
                    with gzip.open(output_gz, 'rb') as f_in:
                        with open(output_bin, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out) #ignore: type
                            print("done")

            print("[Gensim]: Loading Word2Vec model..", end=" ")
            self.model = KeyedVectors.load_word2vec_format(word2vec_model_name, binary=True)
            print("done")
        else:
            print("[Gensim]: Specify Arguments accepted. Gensim disabled.")

    def compare_words_word2vec(self, word1, word2, model = None) -> float|None:
        model_state = self.model_null_safe(model)
        if not model_state:
            return None

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
    ) -> tuple[bool|None, float|None]:
        similarity = self.compare_words_word2vec(word1, word2, model)
        if similarity is None:
            return None, None
        match = similarity >= threshold
        return match, similarity
default = Gensim()