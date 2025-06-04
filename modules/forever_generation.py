import abc
import asyncio
from typing import *
from utils import *
from modules.generate import Txt2imgAPI

class ForeverGeneration(abc.ABC):
  def __init__(self, payload: dict, *args, **kwargs):
    self._payload = payload.copy()
    self.is_generating = False
    self._stop_event = asyncio.Event()
  
  
  @abc.abstractmethod
  async def get_payload(self) -> dict:
    raise NotImplementedError
  
    
  async def generate_forever(
    self, **override_payload
  ) -> AsyncGenerator[dict, None]:
    """
    payloadを取得する関数を受け取り生成を続ける
    
    """
    if self.is_generating:
      printerr("Already generating, cannot start a new generation.")
      return
    
    text = ""
    self.is_generating = True
    self._stop_event.clear()
    default_payload = self._payload | override_payload
    api = Txt2imgAPI(
      payload=default_payload
    )
    
    try:
      while not self._stop_event.is_set() and self.is_generating:
        payload = await self.get_payload()
        async for i in api.generate_with_progress(**payload):
          if i[0] is False: # 終わってないなら
            progress = i[2]
            # println(f"[in forever_generation.py] Progress: {progress}")
            yield {"success": "in_progress", "progress": progress, "ok": False}
            continue
          elif i[0] is None: # エラー
            yield {"success": "error", "ok": False}
            continue
          elif i[0] is True: # 終わったら
            result = i[1]
            yield {"success": "completed", "result": result, "ok": True}
            break
        await asyncio.sleep(1.5) # OSErrorを防ぐ
    except Exception as e:
      print_critical(f"Error generating image: {e}")
      raise
    finally:
      self.is_generating = False
      self._stop_event.set()
      print("Generation stopped.")
    return
  
  async def stop_generation(self):
    self._stop_event.set()
    self.is_generating = False
    println("Generation stopped by user.")
  
  async def start_generation(self) -> AsyncGenerator[dict, None]:
    if self.is_generating:
      printerr("Already generating, cannot start a new generation.")
      return
    println("Generation started.")
    async for item in self.generate_forever():
      yield item