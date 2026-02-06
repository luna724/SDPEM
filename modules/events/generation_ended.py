from logger import critical
from modules.event import Event, EventType
from typing import Literal, TYPE_CHECKING
import traceback
import pydantic
from modules.utils.zipper import PromptScore, BooruResult
from modules.config import get_config
config = get_config()


class OnGenerationEndedEvent(EventType):
  event_name = "generation_ended"
  infotxt: str
  params: dict
  end_type: Literal["interrupt", "booru_interrupt", "complete"]
  rate: Literal["perfect", "ok", "bad", "worst"] = "undefined"
  script: Literal["sdpem/lora", "sdpem/image", "sdpem/mlora", "sdpem/db", "webui", "webui/api", "other"] = "undefined"
  
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
    
  
  async def auto_trig(
    self,
    infotext: str, params: dict, pem_params: dict = None,
    endtype = "complete", rate = "undefined", script = "undefined", pscores: dict | list[tuple] | list["PromptScore"] = None, booru: dict | list[dict] | None | "BooruResult" = None, ts: float | int = None, image_fp: str = None,
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
          pscores = [PromptScore(*t) for t in pscores]
        
        ev.pem_params = pem_params
        ev.prompt_score = pscores
      
      if config.save_booru_out:
        if isinstance(booru, dict):
          booru = BooruResult(**booru)
        elif isinstance(booru, list):
          booru = BooruResult(
            tags=[PromptScore(tag=k, score=v) for k, v in booru[0].items()],
            characters=[PromptScore(tag=k, score=v) for k, v in booru[1].items()],
          )
        elif booru is None:
          
      
    except pydantic.ValidationError:
      critical("OnGenerationEnded: Invalid event parameters")
      traceback.print_exc()
      return

onGenerationEnded = OnGenerationEnded()