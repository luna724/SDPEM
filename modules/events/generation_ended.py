from logger import critical
from modules.event import Event, EventType
from typing import Literal, TYPE_CHECKING
import traceback
import pydantic
from modules.generate import GenerationResult
from modules.utils.zipper import PromptScore, BooruResult
from modules.config import get_config
config = get_config()


class OnGenerationEndedEvent(EventType):
  event_name:str = "generation_ended"
  infotxt: str
  params: dict
  end_type: Literal["interrupt", "booru_interrupt", "complete"]
  rate: Literal["perfect", "ok", "bad", "worst", "undefined"] = "undefined"
  script: Literal["sdpem/lora", "sdpem/image", "sdpem/mlora", "sdpem/db", "webui", "webui/api", "other", "undefined"] = "undefined"
  
  # only for sdpem #
  prompt_score: list["PromptScore"] = None # 実行当時の利用されたスコアを保持
  pem_params: dict = None
  
  # based on user config #
  # saveBooruOutput
  booru_out: "BooruResult" = None 
  
  # 実際のプロンプト -> booru結果で失ったプロンプト、追加されたプロンプト
  # calcDiffOnSave
  lost_tags: list["PromptScore"] = None 
  ghost_tags: list["PromptScore"] = None
  
  # dcLog
  luuid: str = None # logのUUID
  ts: float = None 

  # imagePathOnLog
  result_images: str = None # 生成結果画像の絶対パス
  

class OnGenerationEnded(Event):
  """
  実際には生成完了時ではなく、各画像の最終処理終了後、または外部hookに対し結果の引き渡しが行われた際に画像ごとに呼ばれる
  
  
  """

  def __init__(self):
    super().__init__()
    self.EventId = 0
    self.accept_events = [OnGenerationEndedEvent]
    self.target_cls = OnGenerationEndedEvent
    
  async def trigger_from_result(
    self, p: GenerationResult, saved: bool,
    image_fp: str | None = None,
    ts: float | int | None = None,
    booru: dict | list | BooruResult | None = None,
    pscores: dict | list | list[PromptScore] | str | None = None,
    pem_params: dict | None = None,
    script: str = "undefined",
    rate: str = "undefined",
    endtype: str | None = None,
  ):
    infotext = getattr(p, "infotext", "")
    params = getattr(p, "raw", getattr(p, "dict", lambda: {})() if hasattr(p, "dict") else (p.model_dump() if hasattr(p, "model_dump") else {}))
    if endtype is None or endtype not in ("interrupt", "booru_interrupt", "complete"):
      endtype = "complete" if saved else "interrupt"

    await self.auto_trig(
      infotext=infotext,
      params=params,
      pem_params=pem_params,
      endtype=endtype,
      rate=rate,
      script=script,
      pscores=pscores,
      booru=booru,
      ts=ts,
      image_fp=image_fp,
    )
  
  async def auto_trig(
    self,
    infotext: str, params: dict, pem_params: dict = None,
    endtype = "complete", rate = "undefined", script = "undefined", pscores: str | dict | list | None = None, booru: dict | list | BooruResult | None = None, ts: float | int | None = None, image_fp: str | None = None,
  ) -> None:
    try:
      ev = OnGenerationEndedEvent(
        infotxt=infotext,
        params=params,
        end_type=endtype,
        rate=rate,
        script=script,
      )
      
      if pem_params is not None:
        if isinstance(pscores, dict):
          pscores = [PromptScore(tag=k, score=v) for k, v in pscores.items()]
        elif isinstance(pscores, list):
          pscores = [PromptScore(*t) if isinstance(t, (tuple, list)) else t for t in pscores]
        
        ev.pem_params = pem_params
        ev.prompt_score = pscores
      
      if config.save_booru_out:
        if isinstance(booru, dict):
          booru = BooruResult(**booru)
        elif isinstance(booru, list):
          tags = [PromptScore(tag=k, score=v) for k, v in booru[0].items()] if len(booru) > 0 and isinstance(booru[0], dict) else []
          chars = [PromptScore(tag=k, score=v) for k, v in booru[1].items()] if len(booru) > 1 and isinstance(booru[1], dict) else []
          rating = [PromptScore(tag=k, score=v) for k, v in booru[2].items()] if len(booru) > 2 and isinstance(booru[2], dict) else []
          threshold = float(booru[3]) if len(booru) > 3 else 0.0
          booru = BooruResult(tags=tags, characters=chars, rating=rating, threshold=threshold)
        if isinstance(booru, BooruResult):
          ev.booru_out = booru
      
      if ts is not None:
        ev.ts = float(ts) if isinstance(ts, (float, int)) else ts
      if image_fp is not None:
        ev.result_images = image_fp
      
      await self.trigger("generation_ended", ev)
    except pydantic.ValidationError:
      critical("OnGenerationEnded: Invalid event parameters")
      traceback.print_exc()
      return

onGenerationEnded = OnGenerationEnded()