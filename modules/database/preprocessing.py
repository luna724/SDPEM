from typing import Optional
from pydantic import BaseModel
import os
import os.path as op
import re
from PIL import Image

from logger import warn, debug
from modules.utils.pnginfo import read_pnginfo
from modules.utils.prompt import separate_prompt
from modules.tagger.predictor import OnnxRuntimeTagger, OnnxTaggerMulti
from modules.utils.tagger import get_rating
from modules.utils.prompt import PromptPiece
from modules.utils.lora_util import is_lora_trigger
from modules.config import get_config
from concurrent.futures import ThreadPoolExecutor
config = get_config()

class CalculationTarget(BaseModel):
  tagCounting: bool = True
  cooccurrenceMatrix: bool = True

class PreProcessor:
  def __init__(
    self, target_dir: os.PathLike, booru_model: str, trustability: float = 1,
    calculation: CalculationTarget = CalculationTarget(),
  ):
    self.target_dir = target_dir
    self.trustability = trustability
    self.calculation = calculation
    self.pred: OnnxRuntimeTagger = OnnxRuntimeTagger(booru_model)
  
  @staticmethod
  def read_pnginfo(i):
    return i.info.get("parameters", "").split("Negative prompt: ")[0].strip()
  
  @staticmethod
  def normalize_tag(tag: str) -> Optional[str | list[str]]:
    tag = tag.strip()
    p = []
    if is_lora_trigger(tag):
      return re.sub(r"(<lora:[^:>]+):[^>]+>", r"\1>", tag)
    elif "<lora:" in tag:
      tags = tag.split()
      for t in tags:
        if is_lora_trigger(t):
          p.append(re.sub(r"(<lora:[^:>]+):[^>]+>", r"\1>", t))
          tag = tag.replace(t, "")
      tag = " ".join(tag.split())
      if tag.strip() == "":
        return p
    
    if any(
      tag == b for b in ["BREAK"]
    ):
      return None
    if any(
      tag.startswith(b) for b in ["score_"]
    ):
      return None
    if any(
      tag.startswith(b) for b in ["BREAK", "ADD"]
    ):
      if "," in tag:  
        tag = ",".join(tag.split(",")[1:])
      elif "\n" in tag:
        tag = "\n".join(tag.split("\n")[1:])
      else:
        tag = " ".join(tag.split()[1:])
      if tag == "," or tag == "\n" or tag == "":
        return None
    
    tag = tag.lower()
    norm = " ".join(tag.replace("_", " ").split())

    # 外側の未エスケープ括弧を削除
    norm = re.sub(r"(?<!\\)^[\(\[\{]+", "", norm)
    norm = re.sub(r"(?<!\\)[\)\]\}]+$", "", norm)

    # 未エスケープの weight を削除
    norm = re.sub(r"(?<!\\):[0-9]+(?:\.[0-9]+)?$", "", norm)

    # 末尾の未エスケープ区切り
    norm = re.sub(r"(?<!\\)[,:]+$", "", norm)
    norm = re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", "", norm)
    
    if "." in norm or "" == norm.strip(): 
      return None 
    
    if len(p) >= 1:
      p.append(norm)
      return p
    return norm
  
  @staticmethod
  def seprompt(p):
    a = []
    if isinstance(p, str):
      p = separate_prompt(p)
    
    for t in p:
      f = PreProcessor.normalize_tag(t)
      if f is not None:
        if isinstance(f, list):
          a.extend(f)
        else:
          a.append(f)
      else:
        debug(f"[PreProc] Skipping: {t}")
    return a
  
  async def prepare(self, c: int = 1):
    if c is None: c = max(1, os.cpu_count() - 2)
    pool = [[], [], []] # prompts, booru inferred, rating
    if self.calculation.cooccurrenceMatrix:
      await self.pred.load_model_cuda()
    
    files = [f for f in os.listdir(self.target_dir) if os.path.splitext(f)[1].lower() == ".png"]
    
    def p(f):
      b = os.path.basename(f)
      cap = op.join(self.target_dir, b + ".txt")
      if op.exists(cap):
        info = open(cap, "r", encoding="utf-8").read()
        prompt = info.split("Negative prompt:")[0].strip()
      else:
        info = self.read_pnginfo(Image.open(op.join(self.target_dir, f)))
        prompt = info
        
        pd = self.pred.predict_sync(
          Image.open(op.join(self.target_dir, f)).convert("RGBA"),
          threshold=config.booru_threshold,
          character_threshold=0.8,
        )
        inferred = pd[0] | pd[1]
        rate, _, _ = get_rating(pd[2], True)
        
        if rate != "?":
          pool[0].append(self.seprompt(prompt))
          pool[1].append(self.seprompt(list(inferred.keys())))
          pool[2].append(rate)
        else:
          warn(f"Skipping {b} due to no rating found.")
          return
    
    with ThreadPoolExecutor(max_workers=c) as executor:
      list(executor.map(p, files))
    
    if self.calculation.cooccurrenceMatrix:
      await self.pred.unload_model()
    
    return pool