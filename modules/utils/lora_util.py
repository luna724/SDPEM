import os 
import json
import re
import os.path as op
import traceback
from typing import *
from shared import api_path
from logger import *
from legacy.modules.lora_metadata_util import LoRAMetadataReader
from safetensors import safe_open
from modules.utils.prompt import PromptPiece
from pathlib import Path
from PIL import Image

LORA_TRIGGER_PATTERN = r"^\<lora\:(.*)?\>$"

class LoRAMetadataReader:
    def __init__(self, fp):
        self.loadable = False
        self.fp = fp
        self.fn = os.path.basename(fp)
        self.metadata = {}
        try:
            with safe_open(os.path.abspath(fp), framework="pt") as f:
                self.metadata = f.metadata()
                self.keys = list(f.keys())
                self.loadable = True
                #print(f"[DEV]: [metadata]: {self.metadata}")
        except Exception:
            critical(f"[ERROR]: Error occurred in parse safetensors")
            traceback.print_exc()

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
        except Exception as e:
            critical(f"Error reading safetensors ({self.fp})")
            raise e

    def isSDXL(self):
        return self.detect_model_ver() == "SDXL1.0"

    def get_output_name(self, blank=None):
        metadata = self.metadata or {}
        output_name = metadata.get("ss_output_name", None)
        if output_name is None:
            output_name = op.splitext(self.fn)[0]
        
        println(f"Detected lora trigger: {output_name}")
        return output_name

    def detect_base_model_for_ui(self):
        """
        safetensors ファイルを読み取り、ベースモデルを判別します。
        """
        try:
            metadata = self.metadata or {}
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
            return "Unknown model"

        except ValueError:
            return "Unknown model"

        except Exception as e:
            critical(f"Error reading safetensors file: {e}")
            traceback.print_exc()
            return "Unknown model"

async def find_lora(lora_name: str, allow_none: bool = True) -> Optional[str | os.PathLike]:
    r"""渡されたLoRA名をシンプルに models/Lora から探す
    
    Path injection warnings are mitigated by:
    - Validating lora_name doesn't contain path traversal sequences (.., /, \)
    - Ensuring the final path is within the models/Lora directory
    
    raise: FileNotFoundError Allow_none=False で見つからなかった場合
    """
    if os.path.exists(lora_name): # TODO: なぜか forever/from loraから絶対パスが渡される場合があるから治す
        return lora_name
    
    lp = os.path.join(api_path, "models/Lora", lora_name)
    
    # Ensure the path is within the Lora directory
    lora_dir = os.path.join(api_path, "models/Lora")
    if not os.path.abspath(lp).startswith(os.path.abspath(lora_dir)):
        if not allow_none:
            raise FileNotFoundError(f"Path traversal attempt detected: {lora_name}")
        return None
    
    if not allow_none and not os.path.exists(lp):
        raise FileNotFoundError(f"LoRA '{lora_name}' not found at {lp}")
    return lp if os.path.exists(lp) else None

async def extract_external_lora_meta(lora_path: str) -> dict:
    r = Path(lora_path).parent
    fn = Path(lora_path).stem
    p = r / f"{fn}.json"
    img = r / f"{fn}.png"
    
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if img.exists():
                    data["image"] = Image.open(img.resolve()).convert("RGBA")
                
                return data
        except Exception as e:
            critical(f"Error reading external LoRA metadata from {p}: {e}")
            traceback.print_exc()
    return {}


async def get_tag_freq_from_lora(lora_name: str, test_frequency: bool = False) -> tuple[dict[str, int]]:
  """[tag_freq, ss_tag_freq]の形式で返す"""
  lora = await find_lora(lora_name, allow_none=False)
  metadata = LoRAMetadataReader(lora)
  if not test_frequency:
    tf = {}
    sstf = {}
    if not metadata.loadable:
        critical(f"LoRA '{lora_name}' is not loadable")
        return tf, sstf
    
    tag_freq = json.loads(metadata.metadata.get("ss_tag_frequency", "{}"))
    ss_freq = json.loads(metadata.metadata.get("tag_frequency", "{}"))
    for k, v in tag_freq.items():
      if isinstance(v, int):
        tf[k] = v
      elif isinstance(v, dict) or isinstance(v, str):
        if isinstance(v, str):
          v = json.loads(v)
        for sub_k, sub_v in v.items():
          tf[sub_k] = sub_v
    for k, v in ss_freq.items():
      if isinstance(v, int):
        sstf[k] = v
      elif isinstance(v, dict) or isinstance(v, str):
        if isinstance(v, str):
          v = json.loads(v)
        for sub_k, sub_v in v.items():
          sstf[sub_k] = sub_v
    return tf, sstf
  
  relative_tag_freq = {}
  relative_ss_tag_freq = {}
  tag_freq = json.loads(metadata.metadata.get("tag_frequency", "{}"))
  ss_tag_freq = json.loads(metadata.metadata.get("ss_tag_frequency", "{}"))
  dataset_info = json.loads(metadata.metadata.get("ss_datasets", "{[{}]}"))
  train_images = dataset_info[0].get("num_train_images", 1)
  for k, v in tag_freq.items():
    if isinstance(v, int):
      relative_tag_freq[k] = v / train_images if v > 0 else 0
    elif isinstance(v, dict) or isinstance(v, str):
      if isinstance(v, str):
        v = json.loads(v)
      for sub_k, sub_v in v.items():
        relative_tag_freq[sub_k] = sub_v / train_images if sub_v > 0 else 0
  for k, v in ss_tag_freq.items():
    if isinstance(v, int):
      relative_ss_tag_freq[k] = v / train_images if v > 0 else 0
    elif isinstance(v, dict) or isinstance(v, str):
      if isinstance(v, str):
        v = json.loads(v)
      for sub_k, sub_v in v.items():
        relative_ss_tag_freq[sub_k] = sub_v / train_images if sub_v > 0 else 0
  return relative_tag_freq, relative_ss_tag_freq

async def read_lora_name(lora_name: str, allow_none: bool = True) -> str:
    """LoRA名を読み取り、存在しない場合は例外を投げる"""
    lora = await find_lora(lora_name, allow_none=allow_none)
    if not lora:
        if allow_none:
            return ""
        raise FileNotFoundError(f"LoRA '{lora_name}' not found")
    meta = LoRAMetadataReader(lora)
    if not meta.loadable:
        if allow_none:
            return ""
        raise ValueError(f"LoRA '{lora_name}' is not loadable")
    output = meta.get_output_name()
    if output is None:
        if allow_none:
            return ""
        raise ValueError(f"LoRA '{lora_name}' has no output name")
    return output
  

def list_lora() -> list[str]:
    """LoRA一覧を取得する"""
    lora_dir = os.path.join(api_path, "models/Lora")
    lora_files = [
        f for f in os.listdir(lora_dir)
        if f.endswith(".safetensors") or f.endswith(".ckpt") or f.endswith(".pt")
    ]
    return lora_files

def has_lora_tags(lora_name: str) -> bool:
    r"""Check if a LoRA has tag metadata
    
    Path injection warnings are mitigated by:
    - Validating lora_name doesn't contain path traversal sequences (.., /, \)
    - Ensuring the final path is within the models/Lora directory
    
    Returns True if the LoRA has either ss_tag_frequency or tag_frequency metadata
    """
    try:
        # Validate lora_name to prevent path traversal
        if not lora_name or '..' in lora_name or '/' in lora_name or '\\' in lora_name:
            critical(f"Invalid LoRA name: {lora_name}")
            return False
        
        lora_path = os.path.join(api_path, "models/Lora", lora_name)
        
        # Ensure the path is within the Lora directory
        lora_dir = os.path.join(api_path, "models/Lora")
        if not os.path.abspath(lora_path).startswith(os.path.abspath(lora_dir)):
            critical(f"Path traversal attempt detected: {lora_name}")
            return False
        
        if not os.path.exists(lora_path):
            return False
        
        metadata = LoRAMetadataReader(lora_path)
        if not metadata.loadable:
            return False
        
        # Check if tag frequency metadata exists
        has_ss_tag = metadata.metadata.get("ss_tag_frequency", "{}") != "{}"
        has_tag = metadata.metadata.get("tag_frequency", "{}") != "{}"
        
        return has_ss_tag or has_tag
    except Exception as e:
        critical(f"Error checking tags for LoRA '{lora_name}': {e}")
        return False

def list_lora_with_tags() -> list[str]:
    """LoRA一覧を取得する (タグを持つもののみ)"""
    all_loras = list_lora()
    return [lora for lora in all_loras if has_lora_tags(lora)]
  
def is_lora_trigger(tag: str | PromptPiece) -> bool:
    if isinstance(tag, str):
        return re.match(LORA_TRIGGER_PATTERN, tag.strip()) is not None
    elif isinstance(tag, PromptPiece):
        return is_lora_trigger(tag.value)
    return False