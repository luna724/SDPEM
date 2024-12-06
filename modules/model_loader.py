import shared
import torch


class ModelLoaderClassUtil:
    """super() をモデル定義より先に呼び出す必要がある"""

    def __init__(self, modular_name: str):
        """super().__init__() をモデル定義より先に呼び出す必要がある"""
        self.model = None
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
