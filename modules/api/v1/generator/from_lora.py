import json
from pydantic import BaseModel
from shared import app, api_path
from typing import *
from fastapi import status
import os
import re
import random

from utils import *
from legacy.modules.lora_metadata_util import LoRAMetadataReader

async def find_lora(lora_name: str, allow_none: bool = True) -> Optional[str | os.PathLike]:
  """渡されたLoRA名をシンプルに models/Lora から探す
  
  raise: FileNotFoundError Allow_none=False で見つからなかった場合
  """
  lp = os.path.join(api_path, "models/Lora", lora_name)
  if not allow_none and not os.path.exists(lp):
    raise FileNotFoundError(f"LoRA '{lora_name}' not found at {lp}")
  return lp if os.path.exists(lp) else None


async def make_blacklist(blacklist: List[str]) -> List[re.Pattern]:
  """ブラックリストを一致しやすい形式に変換する"""
  if not blacklist:
    return []
  return [re.compile(rf"^\s*{re.escape(tag)}\s*$", re.IGNORECASE) for tag in blacklist]


async def get_tag_freq_from_lora(lora_name: str, test_frequency: bool = False) -> Tuple[Dict[str, int]]:
  """[tag_freq, ss_tag_freq]の形式で返す"""
  lora = await find_lora(lora_name, allow_none=False)
  metadata = LoRAMetadataReader(lora)
  if not test_frequency:
    tf = {}
    sstf = {}
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
  
  
class _GetPromptFromLoRA(BaseModel):
  lora_name: List[str]
  use_relative_frequency: bool = True
  
@app.post("/v1/prompt_from_lora")
async def get_prompt_from_lora(rq: _GetPromptFromLoRA):
  """
  指定したLoRAからプロンプトをすべて取得する
  """
  tf = {}
  sstf = {}
  for lora in rq.lora_name:
    tag_freq, ss_tag_freq = await get_tag_freq_from_lora(lora, test_frequency=rq.use_relative_frequency)
    tf.update(tag_freq)
    sstf.update(ss_tag_freq)
    
  return {
    "tag_frequency": tf,
    "ss_tag_frequency": sstf
  }, status.HTTP_200_OK


class _GeneratePromptFromFrequency(BaseModel):
  frequency: Dict[str, int]
  blacklist: List[str] = []
  black_patterns: List[str] = []
  blacklisted_weight: int | float = 0
  weight_multiplier: int | float = 2
  weight_multiplier_target: tuple[int, int] = (1, 12) # min, max
  disallow_duplicate: bool = True
  header: str = ""
  footer: str = ""
  tag_count: int = 7
  base_chance: int | float = 10
@app.post("/v1/generator/lora/frequency2prompt")
async def generate_prompt_from_frequency(rq: _GeneratePromptFromFrequency):
  """
  渡された tag_frequency からプロンプトを生成する
  """
  blacklists: list[re.Pattern] = await make_blacklist(rq.blacklist) + [re.compile(pattern, re.IGNORECASE) for pattern in rq.black_patterns]
  if not rq.frequency and len(rq.frequency) < 1:
    return {"success": False, "message": "No frequency data provided"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  if rq.tag_count < 1:
    return {"success": False, "message": "Tag count must be at least 1"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  if rq.base_chance <= 0:
    return {"success": False, "message": "Base chance must be greater than 0"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  
  rt = []
  for tag, weight in rq.frequency.items():
    final_multiplier = 1
    if any(p.search(tag) for p in blacklists):
      final_multiplier *= rq.blacklisted_weight
    if rq.weight_multiplier_target[0] <= weight <= rq.weight_multiplier_target[1]:
      final_multiplier *= rq.weight_multiplier
    weight = (weight * final_multiplier) / (100 * rq.base_chance)
    if weight > 0:
      rt.append((tag, weight))
    
  def get_weight(t: tuple[str, int | float]) -> int | float: return t[1]
  resized_tags = sorted(rt, key=get_weight)
  if len(resized_tags) < 1 or (rq.disallow_duplicate and len(resized_tags) < rq.tag_count):
    return {"success": False, "message": "Not enough tags found"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  
  prompts = []
  while len(prompts) < rq.tag_count:
    for (tag, weight) in resized_tags:
      if len(prompts) >= rq.tag_count:
        break
      if random.random() < weight and (not rq.disallow_duplicate or not tag in prompts):
        if random.random() < 0.05: # 5% でプロンプトに重みづけ
          tag = f"({tag}:{random.randrange(40, 140, 1)/100})" #崩壊しない範囲
        prompts.append(tag)
  if len(prompts) < 1:
    return {"success": False, "message": "No tags selected"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  result = rq.header.strip(", ") + ", " + ", ".join(prompts) + ", " + rq.footer.strip(", ")
  return {
    "success": True,
    "prompt": result
  }, status.HTTP_200_OK
    
class _GeneratePromptFromLoRA(BaseModel):
  lora_name: List[str]
  blacklist: List[str] = []
  black_patterns: List[str] = [] # patternLike
  blacklisted_weight: int | float = 0
  weight_multiplier: int | float = 2
  weight_multiplier_target: tuple[int, int] = (1, 12) # min, max
  disallow_duplicate: bool = True
  header: str = ""
  footer: str = ""
  max_tags: int = 7
  base_chance: int | float = 10
  add_lora_name: bool = True
  lora_weight: int | float = 0.5

  def cast_into_frequency_model(self, frequency: dict[str, int]) -> _GeneratePromptFromFrequency:
    """_GeneratePromptFromLoRA を _GeneratePromptFromFrequency に変換する"""
    return _GeneratePromptFromFrequency(
      frequency=frequency,
      blacklist=self.blacklist,
      black_patterns=self.black_patterns,
      blacklisted_weight=self.blacklisted_weight,
      weight_multiplier=self.weight_multiplier,
      weight_multiplier_target=self.weight_multiplier_target,
      disallow_duplicate=self.disallow_duplicate,
      header=self.header,
      footer=self.footer,
      tag_count=self.max_tags,
      base_chance=self.base_chance
    )
@app.post("/v1/generator/lora/lora2prompt")
async def generate_prompt_from_lora(rq: _GeneratePromptFromLoRA):
  if not rq.lora_name or len(rq.lora_name) < 1:
    return {"success": False, "message": "No LoRA names provided"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  frequency = {}
  unknown_lora = []
  for lora_name in rq.lora_name:
    lora = await find_lora(lora_name, allow_none=True)
    if not lora:
      printwarn("Unknown LoRA:", lora_name)
      unknown_lora.append(lora_name)
      continue
    tag_freq, ss_tag_freq = await get_tag_freq_from_lora(lora)
    frequency.update(tag_freq)
    frequency.update(ss_tag_freq)

  if len(frequency) < 1:
    return {"success": False, "message": "No tags found in the provided LoRA(s)"}, status.HTTP_422_UNPROCESSABLE_ENTITY
  
  frequency_model = rq.cast_into_frequency_model(frequency=frequency)
  response, s = await generate_prompt_from_frequency(frequency_model)
  if not response["success"]:
    return response, s

  prompt = response["prompt"]
  if rq.add_lora_name:
    for lora_name in rq.lora_name:
      lora_name = await read_lora_name(lora_name, allow_none=True)
      if lora_name is None:
        printwarn("Unknown LoRA name:", lora_name)
        continue
      prompt += f", <lora:{lora_name}:{rq.lora_weight}>"
  return {
    "success": True,
    "prompt": prompt
  }, status.HTTP_200_OK


@app.post("/v1/items/lora/names")
async def get_lora_names(rq: _GetPromptFromLoRA):
  lora_names = []
  for lora_name in rq.lora_name:
    lora_name = await read_lora_name(lora_name, allow_none=True)
    if lora_name is None:
      printwarn("Unknown LoRA name:", lora_name)
      continue
    lora_names.append(lora_name)
  return {
    "success": True,
    "names": lora_names
  }, status.HTTP_200_OK









