from fastapi import status
from pydantic import BaseModel
from shared import app, api_path
from typing import *
import re

from logger import *
import random
from modules.utils.lora_util import find_lora, read_lora_name, get_tag_freq_from_lora

async def make_blacklist(blacklist: List[str]) -> List[re.Pattern]:
  """ブラックリストを一致しやすい形式に変換する"""
  if not blacklist:
    return []
  return [re.compile(rf"^\s*{re.escape(tag)}\s*$", re.IGNORECASE) for tag in blacklist]


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
      warn("Unknown LoRA:", lora_name)
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
        warn("Unknown LoRA name:", lora_name)
        continue
      prompt += f", <lora:{lora_name}:{rq.lora_weight}>"
  return {
    "success": True,
    "prompt": prompt
  }, status.HTTP_200_OK
  