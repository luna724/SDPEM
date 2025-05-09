from transformers import AutoTokenizer, AutoModelForCausalLM

from modules.models.model_loader import ModelLoaderClassUtil
import shared


class OLlama(ModelLoaderClassUtil):
    def __init__(self):
        super().__init__("MiniCPM3-4B")
        self.size = "4"

        load_state = not (shared.args.nogpt2 or shared.args.nolm)
        if load_state:
            model_name = f"openbmb/MiniCPM3-4B"
            print(f"[OLlama]: Loading OLlama/{self.size}B model.. ", end="")

            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            print("done")
            self._send_model_to_cpu()
        else:
            print("[OLlama]: Specify Arguments accepted.")

    def infer(
            self,
            prompt: str, max_length: int = 100,
            temp: float = 0.7, top_k: int = 70, top_p: float = 0.9
    ) -> str:
        inputs = self.tokenizer.encode(
            prompt, return_tensors="pt"
        )
        outputs = self.model.generate(
            inputs,
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


default = OLlama()