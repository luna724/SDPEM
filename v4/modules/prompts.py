from typing import *
import re

def rebuild_prompts(
  prompts: List[str], separator: str = ", "
) -> str:
  """Rebuild prompt from prompts
  """
  return separator.join(prompts).strip(separator)


def reObf_prompt(
  prompt:str, separator: str ="?usr"
) -> List[tuple]:
  """
  プロンプトを処理可能形式に変換する
  LBWには新記入式にのみ対応
  
  出力形式
  [
    (piece, weight, isLoRA, LoRAWeight, LBWitems), ..
  ]
  """
  prompts = []
  
  for (i, pp) in enumerate(prompt.split(",")):
    p = pp.strip()

    # 初期化
    weight: float|None = None
    isLoRA: bool       = False
    LoRAWeight: float  = 1.0
    LBWItems: str|None = None
    
    if p.startswith("<lora:"):
      isLoRA = True
      
      if ":lbw" in p:
        LBWItems = ":lbw"
        LBWItems += p.split(":lbw")[1]
        p = p.split(":lbw")[0] + ">"
      
      ptrn = r"^<lora:.*:([\d\.]+)>$"
      matches = re.match(ptrn, p)
      if matches:
        LoRAWeight = float(matches.group(1))
    
    else:
      ptrn = r"^[\[\(]?.*?:([\d]+(\.[\d]+)?),?[\]\)]?,?$"
      matches = re.match(ptrn, p)
      if matches:
        weight = float(matches.group(1))
    
    prompts.insert(i, (pp, weight, isLoRA, LoRAWeight, LBWItems))
  return prompts