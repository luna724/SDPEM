from modules.util import Util
from PIL import Image

class BackgroundDetailer(Util):
    def __init__(self):
        super().__init__()

    def run_adetailer_mask(
            self,
            base_image: Image.Image, threshold: float, model_name: str, invert_mask: bool = False
    ) -> Image.Image:
        """
        背景のマスクを自動検出する
        """
        if model_name.startswith("internal/"):
            model_name = model_name[9:]
