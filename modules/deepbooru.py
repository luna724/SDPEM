import requests
import torch
import PIL.Image as Image
import numpy as np
import os
import tqdm
import gc
from typing import *

import shared
from modules.model_loader import ModelLoaderClassUtil
from modules.torch_deepbooru import DeepDanbooruModel


class Deepbooru(ModelLoaderClassUtil):
    def __init__(self, deepbooru_model_name=None):
        super().__init__("Deepbooru")
        load_state = not (shared.args.no_booru or shared.args.nolm)
        if load_state:
            print(
                "[Deepbooru]: [WARN]: Currently, Deepbooru can only accept torch-nn like model"
            )
            self.model = DeepDanbooruModel()
            if deepbooru_model_name is None:
                deepbooru_model_name = shared.model_file["deepbooru"]
            if deepbooru_model_name == "a1111_model-resnet_custom_v3.pt":
                if not os.path.exists(deepbooru_model_name):
                    print("[Deepbooru]: Deepbooru model not found. downloading...", end=" ")
                    url = "https://github.com/AUTOMATIC1111/TorchDeepDanbooru/releases/download/v1/model-resnet_custom_v3.pt"
                    output_path = deepbooru_model_name
                    try:
                        content = requests.get(url, stream=True)
                        content.raise_for_status()
                        with open(output_path, "wb") as f:
                            for chunk in content.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print("done")
                    except requests.RequestException as e:
                        print(f"error\n[Deepbooru]: Exception in Model downloading: {e}")
                        return  # モデルのダウンロードに失敗した場合、初期化を中断
            print("[Deepbooru]: Loading Deepbooru models..", end=" ")
            self.model.load_state_dict(torch.load(deepbooru_model_name))
            self.model.eval()

            self.model.cpu()
            if shared.args.half_booru:
                self.model.half()

            if hasattr(self.model, "tags") and self.model.tags:
                self.tags = self.model.tags
                print("[Deepbooru]: Successfully loaded tag lists from Model")
            else:
                self.tags = self.load_tag_names()
                self.model.tags = self.tags
                print("[Deepbooru]: Successfully loaded tag lists from file")
            print("done")
        else:
            print("[Deepbooru]: Specify Arguments accepted. Deepbooru disabled.")
            self.tags = []

    @staticmethod
    def load_tag_names() -> List[str]:
        """Code by. GPT-o1-mini
        タグ名のリストをロードします。
        オプションとしてモデル内のタグが利用できない場合に使用されます。

        Returns:
            List[str]: タグ名のリスト。
        """
        tags_file = shared.model_file.get(
            "deepbooru_tags", "configs/deepbooru_default.tags.txt"
        )
        if not os.path.exists(tags_file):
            print(f"[Deepbooru]: tag file '{tags_file}' does not exists.")
            return []

        try:
            with open(tags_file, "r", encoding="utf-8") as f:
                tags = [line.strip() for line in f if line.strip()]
            return tags
        except Exception as e:
            print(f"[Deepbooru]: Error during load tag file ({e})")
            return []

    def get_tags(self, image: Image.Image, threshold=0.5) -> dict:
        """
        画像からタグを取得します。

        Args:
            image (PIL.Image.Image): タグを取得する対象の画像。
            override_model (torch.nn.Module, optional): デフォルトのDeepbooruモデルをオーバーライドするモデル。
            threshold (float, optional): タグを有効とみなす閾値。デフォルトは0.5。

        Returns:
            List[Tuple[str, float]]: 予測されたタグとその確率のリスト。
        """
        model_state = self.model_null_safe()
        if not model_state:
            return []
        model = self.cache_vram()

        # 画像の前処理
        resized_image = image.convert("RGB").resize((512, 512))
        arr = np.expand_dims(np.array(resized_image, dtype=np.float32), 0) / 255

        # 実行
        with torch.no_grad(), torch.autocast(self.dev_type):
            x = torch.from_numpy(arr).to(self.device)

            # first run
            y = self.model(x)[0].detach().cpu().numpy()

            # 平均値を算出
            for n in tqdm.tqdm(range(10)):
                model(x)

        probability_dict = {}

        for tag, p in zip(self.model.tags, y):
            if p < threshold:
                continue
            probability_dict[tag] = p

        # tags = [tag for tag, _ in sorted(probability_dict.items(), key=lambda x: -x[1])]
        self.clean_vram()
        return probability_dict

    def clean_vram(self) -> None:
        """
        Deepbooruモデルをcpuに移動し、VRAMを開放する
        """
        if shared.deepbooru_dont_keep_models_in_ram:
            self.model.to("cpu")
            torch.cuda.empty_cache()

    def cache_vram(self) -> DeepDanbooruModel:
        """
        Deepbooruモデルをcudaに移動し、GPU処理を可能にする処理を可能にする
        """
        return self.model.to(self.device)

    def interrogate(self, image: Image.Image, threshold: float = 0.75) -> dict:
        """Deepbooruの実行
        image, threshold を受け取り、タグをキー、値をthresholdとする辞書を返す
        """
        self.cache_vram()
        probability_dict = self.get_tags(image, threshold=threshold)
        self.clean_vram()

        tags = [tag for tag, _ in sorted(probability_dict.items(), key=lambda x: -x[1])]
        res = {}
        for tag in tags:
            prob = probability_dict[tag]
            tag_formatted = tag.replace("_", " ")
            res[tag_formatted] = prob
        return res
default = Deepbooru()
