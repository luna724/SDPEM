import json
import random
import re
from pydantic import BaseModel
from shared import app, api_path
from typing import *
from fastapi import status
from fastapi.responses import JSONResponse
from logger import *
from modules.utils.lora_util import find_lora, get_tag_freq_from_lora, read_lora_name

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
  return JSONResponse(
    {
    "tag_frequency": tf,
    "ss_tag_frequency": sstf
    },
    status.HTTP_200_OK,
    media_type="application/json"
  )
  
class _GeneratePromptFromFrequency(BaseModel):
  frequency: Dict[str, int]
  blacklist: List[str] = []
  blacklisted_weight: int | float = 0
  weight_multiplier: int | float = 2
  weight_multiplier_target: tuple[int, int] = (1, 12) # min, max
  disallow_duplicate: bool = True
  header: str = ""
  footer: str = ""
  tag_count: int = 7
  base_chance: int | float = 10
  prompt_weight_chance: float = 0.05
  prompt_weight_range: tuple[int|float, int|float] = (0.5, 1.5)
# v1.1
# blacklistの設定をより柔軟に, prompt_weightのオプション化
@app.post("/v1_1/generator/lora/frequency2prompt")
async def generate_prompt_from_frequency(rq: _GeneratePromptFromFrequency):
  """
  渡された tag_frequency からプロンプトを生成する
  """
  blacklists: list[re.Pattern] = [re.compile(tag, re.IGNORECASE) for tag in rq.blacklist]
  if not rq.frequency or len(rq.frequency) < 1:
    return JSONResponse(
      {"success": False, "message": "No frequency data provided"}, 
      status.HTTP_422_UNPROCESSABLE_ENTITY,
      media_type="application/json"
    )
  if rq.tag_count < 1:
    return JSONResponse(
      {"success": False, "message": "Tag count must be at least 1"},
      status.HTTP_422_UNPROCESSABLE_ENTITY,
      media_type="application/json"
    )
  if rq.base_chance <= 0:
    return JSONResponse(
      {"success": False, "message": "Base chance must be greater than 0"},
      status.HTTP_422_UNPROCESSABLE_ENTITY,
      media_type="application/json"
    )

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
    return JSONResponse(
      {"success": False, "message": "Not enough tags found"},
      status.HTTP_422_UNPROCESSABLE_ENTITY,
      media_type="application/json"
    )

  prompts = []
  while len(prompts) < rq.tag_count:
    for (tag, weight) in resized_tags:
      if len(prompts) >= rq.tag_count:
        break
      if random.random() < weight:
        if rq.disallow_duplicate and tag in prompts:
          continue
        if random.random() < rq.prompt_weight_chance:
          pm = rq.prompt_weight_range[0]
          pmx = rq.prompt_weight_range[1]
          if pm >= pmx:
            pmx = pm
          tag = f"({tag}:{random.uniform(pm, pmx):.2f})"
        prompts.append(tag)
  if len(prompts) < 1:
    return JSONResponse(
      {"success": False, "message": "No tags selected"},
      status.HTTP_422_UNPROCESSABLE_ENTITY
    )
  result = rq.header.strip(", ") + ", " + ", ".join(prompts) + ", " + rq.footer.strip(", ")
  return JSONResponse(
    {
      "success": True,
      "prompt": result.lstrip(", ").rstrip(", ")
    },
    status.HTTP_200_OK
  )

class _GeneratePromptFromLoRA(BaseModel):
  lora_name: List[str]
  blacklist: List[str] = []
  blacklisted_weight: int | float = 0
  weight_multiplier: int | float = 1.5
  weight_multiplier_target: tuple[int, int] = (1, 12) # min, max
  disallow_duplicate: bool = True
  header: str = ""
  footer: str = ""
  tag_count: int = 7
  base_chance: int | float = 10
  add_lora_name: bool = False
  lora_weight: str | int | float = "0.5"
  prompt_weight_chance: float = 0.05
  prompt_weight_range: tuple[int|float, int|float] = (0.5, 1.5)

  def cast_into_frequency_model(self, frequency: dict[str, int]) -> _GeneratePromptFromFrequency:
    """_GeneratePromptFromLoRA を _GeneratePromptFromFrequency に変換する"""
    return _GeneratePromptFromFrequency(
      frequency=frequency,
      blacklist=self.blacklist,
      blacklisted_weight=self.blacklisted_weight,
      weight_multiplier=self.weight_multiplier,
      weight_multiplier_target=self.weight_multiplier_target,
      disallow_duplicate=self.disallow_duplicate,
      header=self.header,
      footer=self.footer,
      tag_count=self.tag_count,
      base_chance=self.base_chance,
      prompt_weight_chance=self.prompt_weight_chance,
      prompt_weight_range=self.prompt_weight_range
    )

# v1.1
# freq v1.1に対応、LoRA Weightをテキストで指定可能に
@app.post("/v1_1/generator/lora/lora2prompt")
async def generate_prompt_from_lora_v11(rq: _GeneratePromptFromLoRA):
  if not rq.lora_name or len(rq.lora_name) < 1:
    return JSONResponse(
      {"success": False, "message": "No LoRA names provided"},
      status.HTTP_422_UNPROCESSABLE_ENTITY
    )
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
    return JSONResponse(
      {"success": False, "message": "No tags found in the provided LoRA(s)"},
      status.HTTP_422_UNPROCESSABLE_ENTITY
    )
  
  frequency_model = rq.cast_into_frequency_model(frequency=frequency)
  f_response = await generate_prompt_from_frequency(frequency_model)
  response = json.loads(f_response.body.decode())
  if not response["success"]:
    return f_response

  prompt = response["prompt"]
  if rq.add_lora_name:
    for lora_name in rq.lora_name:
      lora_name = await read_lora_name(lora_name, allow_none=True)
      if lora_name is None:
        warn("Unknown LoRA name:", lora_name)
        continue
      prompt += f", <lora:{lora_name}:{str(rq.lora_weight)}>"
  return JSONResponse(
    {"success": True, "prompt": prompt},
    status.HTTP_200_OK
  )


@app.post("/v1/items/lora/names")
async def get_lora_names(rq: _GetPromptFromLoRA):
  lora_names = []
  for lora_name in rq.lora_name:
    lora_name = await read_lora_name(lora_name, allow_none=True)
    if lora_name is None:
      warn("Unknown LoRA name:", lora_name)
      continue
    lora_names.append(lora_name)
  return JSONResponse(
    {
      "success": True,
      "names": lora_names
    },
    status.HTTP_200_OK
  )









