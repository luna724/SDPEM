import os
import json
import pyjson5 as json5
from pydantic import BaseModel, Field
from typing import Literal

class GlobalConfig(BaseModel):
  # /config/global.json5
  db_dir: str = Field(default="./assets/db")
  save_booru_out: bool = Field(default=True)
  calc_diff_on_save: bool = Field(default=True)
  log_discriminator: bool = Field(default=True)
  save_image_path: bool = Field(default=True)
  
  embed_pnginfo: bool = Field(default=True)

  booru_online_ram: int = Field(default=2048) # MB 
  booru_cuda_inference_memory_limit: int = Field(default=2048) # MB
  booru_device: Literal["cuda", "cpu"] = Field(default="cuda")

def save_gconf(c: GlobalConfig):
  with open("config/global.json5", "w", encoding="utf-8") as f:
    f.write(c.model_dump_json())

def sanitize_config(c: GlobalConfig) -> GlobalConfig:
  if c.db_dir:
    if not os.path.isabs(c.db_dir):
      c.db_dir = os.path.abspath(c.db_dir)
  
  save_gconf(c)
  return c

def load_gconf() -> GlobalConfig: 
  global gConf
  gConf = sanitize_config(GlobalConfig(**json5.load(open("config/global.json5", "r", encoding="utf-8"))))
  return gConf

gConf = sanitize_config(load_gconf())

def get_config(): # optional but recommended
  return gConf