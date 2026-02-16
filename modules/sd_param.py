from modules.api.v1.items import sdapi
from modules.utils.health import a1111
import os
import json

cache_path = os.path.abspath("./assets/sd_param.json")
def read_cache():
  if not os.path.exists(cache_path):
    return {}
  
  with open(cache_path, "r", encoding="utf-8") as f:
    return json.load(f)

def write_cache(k: str, v):
  data = read_cache()
  data[k] = v
  with open(cache_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
  return v

async def get_sampler(force_sdapi: bool = False):
  if force_sdapi or a1111.is_alive:
    return write_cache("sampler", (await sdapi.get_samplers())[0])
  
  return read_cache().get("sampler", [
    "DPM++ 2M",
    "DPM++ SDE",
    "DPM++ 2M SDE",
    "DPM++ 2M SDE Heun",
    "DPM++ 2S a",
    "DPM++ 3M SDE",
    "Euler a",
    "Euler",
    "LMS",
    "Heun",
    "DPM2",
    "DPM2 a",
    "DPM fast",
    "DPM adaptive",
    "Restart",
    "HeunPP2",
    "IPNDM",
    "IPNDM_V",
    "DEIS",
    "DDIM",
    "DDIM CFG++",
    "PLMS",
    "UniPC",
    "LCM",
    "DDPM"
])
  
async def get_scheduler(force_sdapi: bool = False):
  if force_sdapi or a1111.is_alive:
    s = (await sdapi.get_schedulers())[0]
    return write_cache("scheduler", s)
  
  return read_cache().get("scheduler", ['Automatic', 'Uniform', 'Karras', 'Exponential', 'Polyexponential', 'SGM Uniform', 'KL Optimal', 'Align Your Steps', 'Simple', 'Normal', 'DDIM', 'Beta', 'Turbo', 'Align Your Steps GITS', 'Align Your Steps 11', 'Align Your Steps 32'])