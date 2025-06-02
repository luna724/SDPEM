from transformers import GPT2LMHeadModel, GPT2Tokenizer

from modules.models.model_loader import ModelLoaderClassUtil
import shared

class GPT2(ModelLoaderClassUtil):
    def __init__(self):
        super().__init__("LGPT2")

        load_state = not (shared.args.nogpt2 or shared.args.nolm)
        if load_state:
            model_name = "gpt2"
            print("[LGPT-2]: Loading LGPT-2 model.. ", end="")

            self.model = GPT2LMHeadModel.from_pretrained(model_name)
            self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            print("done")
            self._send_model_to_cpu()
        else:
            print("[LGPT-2]: Specify Arguments accepted. LGPT-2 disabled.")

    def infer(
            self,
            prompt: str, max_length: int = 100,
            temp: float = 0.7, top_k: int = 70, top_p: float = 0.9
    ) -> str:
        inputs = self.tokenizer.encode(
            prompt, return_tensors="pt"
        )
        pti = pad_token_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id
        attention_mask = inputs.ne(pti).long()
        outputs = self.model.generate(
            inputs,
            attention_mask=attention_mask,
            max_length=max_length,
            temperature=temp,
            top_k=top_k,
            top_p=top_p,
            pad_token_id=self.tokenizer.eos_token_id
        )
        result = self.tokenizer.decode(
            outputs[0], skip_special_tokens=True
        )
        return result


default = GPT2()