from modules.api.v1.items import sdapi
from modules.utils.health import a1111
import os
import json

cache_path = os.path.abspath("./assets/sd_param.json")
async def get_sampler(force_sdapi: bool = False):
  if force_sdapi or a1111.is_alive:
    return (await sdapi.get_samplers())[0]
  
  