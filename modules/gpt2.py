from transformers import GPT2LMHeadModel, GPT2Tokenizer

from modules.model_loader import ModelLoaderClassUtil
import shared

class GPT2(ModelLoaderClassUtil):
    def __init__(self):
        super().__init__("GPT2")

        load_state = shared.args.nolm
