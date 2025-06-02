from transformers import PreTrainedModel

import shared
import torch


class ModelLoaderClassUtil:
    """super() をモデル定義より先に呼び出す必要がある"""

    def __init__(self, modular_name: str):
        """super().__init__() をモデル定義より先に呼び出す必要がある"""
        self.model = None
        self.model_in_cuda: bool = True
        self.head = f"[{modular_name}]: "

        self.dev_type = "cuda"
        self.device = torch.device(self.dev_type)

    def model_null_safe(self, model=None):
        """
        モデルが正しくロードされているかを確認します。

        Returns:
            bool: モデルがロードされていればTrue、そうでなければFalse。
        """
        self_model = getattr(self, "model", None)
        model = model or self_model

        if model is None:
            return False
        else:
            print(self.head + "This modules Disabled. (but called)")
            return True

    def _send_model_to_cpu(self):
        if shared.args.high_vram:
            print(f"[Model-CPU-sender]: --high_vram received. Model CPU sending are stopped.")
            return

        if not self.model_in_cuda: return

        if isinstance(self.model, PreTrainedModel):
            print("[Model-CPU-sender]: Sending Model to CPU.. ", end="")
            self.model.cpu()
            self.model_in_cuda = False
            print("done")
            return

        else:
            print(f"[Model-CPU-sender]: [ERROR]: [{type(self.model)}]: pem hasn't support this format.")
            return

    def _send_model_to_cuda(self):
        if self.model_in_cuda: return

        if isinstance(self.model, PreTrainedModel):
            if shared.args.cpu:
                if not shared.args.high_vram:
                    print(f"[Model-CUDA-sender]: --cpu received. models keep in CPU.")
            print("[Model-CUDA-sender]: Sending Model to CUDA.. ", end="")
            self.model.cuda()
            self.model_in_cuda = True
            return

        else:
            print(f"[Model-CUDA-sender]: [ERROR]: [{type(self.model)}]: pem hasn't support this format.")
            return