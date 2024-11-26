import os.path
from importlib.metadata import metadata
from typing import *
from safetensors.torch import safe_open, load_file

class LoRAMetadataReader:
    def __init__(self, fp):
        self.loadable = False
        self.fp = fp
        try:
            with safe_open(os.path.abspath(fp), framework="pt") as f:
                self.metadata = f.metadata()
                self.keys = list(f.keys())
                self.loadable = True
                #print(f"[DEV]: [metadata]: {self.metadata}")
        except Exception as e:
            print(f"[ERROR]: Error occurred in parse safetensors: ", end="")
            print(e)

    def detect_model_ver(self):
        """"""
        try:
            metadata = self.metadata
            keys = self.keys

            if metadata:
                base_model_version = metadata.get("ss_base_model_version", "").lower()
                if "sdxl" in base_model_version or "xl" in base_model_version:
                    return "SDXL1.0"
                elif "sd_v1" in base_model_version or "1.5" in base_model_version:
                    return "SD1.5"

            if any("transformer.text_model.encoder.main_layers" in key for key in keys) or \
                    any("1024" in key for key in keys):
                return "SDXL1.0"

            if any("transformer.text_model.encoder.layers" in key for key in keys) or \
                    "lora_te_text_model_encoder_layers_0_mlp_fc1" in keys[0]:
                return "SD1.5"

            raise ValueError(f"Unknown Model type ({self.fp})")
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"Error reading safetensors ({self.fp})")
            raise e

    def isSDXL(self):
        return self.detect_model_ver() == "SDXL1.0"

    def get_output_name(self, blank=None):
        metadata = self.metadata
        output_name = metadata.get("ss_output_name", blank)
        print(f"Detected lora trigger: {output_name}")
        return output_name

    def detect_base_model_for_ui(self):
        """
        safetensors ファイルを読み取り、ベースモデルを判別します。
        """
        try:
            metadata = self.metadata
            keys = self.keys

            # ベースモデル判定ロジック
            if metadata:
                base_model_version = metadata.get("ss_base_model_version", "").lower()
                if "sdxl" in base_model_version or "xl" in base_model_version:
                    return "SDXL 1.0"
                elif "sd_v1" in base_model_version or "1.5" in base_model_version:
                    return "SD 1.5"

            # レイヤー名や次元数で判定
            if any("transformer.text_model.encoder.main_layers" in key for key in keys) or \
                    any("1024" in key for key in keys):
                return "SDXL 1.0"

            if any("transformer.text_model.encoder.layers" in key for key in keys) or \
                    "lora_te_text_model_encoder_layers_0_mlp_fc1" in keys[0]:
                return "SD 1.5"

            # 判定できない場合
            return "Unknown model"

        except ValueError:
            return "Unknown model"

        except Exception as e:
            print(f"Error reading safetensors file: {e}")
            return "Error"