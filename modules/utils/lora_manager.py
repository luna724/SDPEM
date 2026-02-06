from PIL import Image
from pathlib import Path
from modules.utils.lora_util import *

class LoRA:
    def __init__(
        self, name: str, fp: Path, metadata: Dict = None, user_info: dict = None, 
        unknown_lora: bool = False
    ):
        self.name = name
        self.filepath = fp
        self.metadata = metadata
        self.user_info = user_info
        self.unknown_lora = unknown_lora

class LoraManager:
    def __init__(self):
        self.LoRAs : Dict[str, LoRA] = {}
        
    async def init_lora(self):
        for fn in list_lora():
            name = op.splitext(fn)[0]
            fp = await find_lora(fn)
            if fp is None: self.LoRAs[name] = LoRA(name, None, unknown_lora=True); continue
            
            meta = LoRAMetadataReader(fp)
            