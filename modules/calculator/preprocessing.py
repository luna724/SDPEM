import asyncio
from typing import Optional
from pydantic import BaseModel
import os
import os.path as op
import re
from PIL import Image
import aiofiles

from logger import warn, debug, info
from modules.utils.pnginfo import read_pnginfo
from modules.utils.prompt import separate_prompt
from modules.tagger.predictor import OnnxRuntimeTagger, OnnxTaggerMulti
from modules.utils.tagger import get_rating
from modules.utils.prompt import PromptPiece
from modules.utils.lora_util import is_lora_trigger
from modules.config import get_config
from concurrent.futures import ThreadPoolExecutor
config = get_config()

class PreProcessor:
  def __init__(
    self, 
    booru_model: str,
    ignore_questionable: bool = True,
    booru_threshold: float = 0.45,
    trustability: float = 1.0,
  ):
    self.ignore_questionable = ignore_questionable
    self.booru_threshold = booru_threshold
    self.trustability = trustability
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
        ignore = ["score_8_up", "score_7_up", "score_9", ""]
        if not t.strip() in ignore:
          debug(f"[PreProc] Skipping: {t}")
    return a
  
  async def prepare(self, dataset_dir: list[str], c: int = 1):
    if c is None: c = max(1, os.cpu_count() - 2)
    pool = [[], [], []] # prompts, booru inferred, rating
    await self.pred.load_model_cuda()
    
    files = []
    for d in dataset_dir:
      if not op.exists(d) or not op.isdir(d):
        info(f"Directory {d} does not exist or is not a directory. Skipping.")
        continue
      for f in os.listdir(d):
        if op.splitext(f)[1].lower() == ".png":
          files.append((d, f))
    
    def p(file):
      basedir = file[0]
      f = file[1]
      b = os.path.basename(f)
      cap = op.join(basedir, b + ".txt")
      
      if op.exists(cap):
        info = open(cap, "r", encoding="utf-8").read()
        prompt = info.split("Negative prompt:")[0].strip()
      else:
        info = self.read_pnginfo(Image.open(op.join(basedir, f)))
        prompt = info
        
      pd = self.pred.predict_sync(
        Image.open(op.join(basedir, f)).convert("RGBA"),
        threshold=self.booru_threshold,
        character_threshold=0.8,
      )
      inferred = pd[0] | pd[1]
      rate, _, _ = get_rating(pd[2], self.ignore_questionable)
      
      if rate != "?":
        pool[0].append(self.seprompt(prompt))
        pool[1].append(self.seprompt(list(inferred.keys())))
        pool[2].append(rate)
      else:
        warn(f"Skipping {b} due to no rating found.")
        return
    
    def run_pool():
      with ThreadPoolExecutor(max_workers=c) as executor:
        list(executor.map(p, files))
    await asyncio.to_thread(run_pool)
    await self.pred.unload_model()
    
    return pool