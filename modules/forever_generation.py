import abc
import asyncio
import traceback
import gradio as gr
from PIL import Image
from typing import *
from logger import debug, error, critical, println
from modules.generate import Txt2imgAPI, GenerationProgress, GenerationResult

class ForeverGenerationResponse:
    def __init__(
        self,
        success: Literal["in_progress", "completed", "error"],
        payload: dict,
        obj = None, progress = None, result = None,
    ) -> None:
        self.success = success
        self.ok = success == "completed"
        
        self.payload = payload
        self.obj = obj
        
        # compat
        self.progress = progress if success == "in_progress" else None
        self.result = result if success == "completed" else None

        # status code
        self.status = len(success)
        self.IN_PROGRESS = len("in_progress")
        self.COMPLETED = len("completed")
        self.ERROR = len("error")

    def get_progress(self) -> GenerationProgress:
        if self.success == "in_progress":
            return self.progress
        raise ValueError("Progress is only available when success is 'in_progress'")
    
    def get_result(self) -> GenerationResult:
        if self.success == "completed":
            return self.result
        raise ValueError("Result is only available when success is 'completed'")

    def parse_error(self) -> Exception:
        if self.success == "error":
            try:
                raise self.obj
            except Exception as e:
                traceback.print_exc()
                critical(f"Error in Forever Generation: {e}")
            finally:
                return self.obj
        raise ValueError("Error is only available when success is 'error'")

    # compat
    def __getitem__(self, key): 
        if key in ["success", "ok", "payload", "progress", "result"]:
            atr = getattr(self, key, None)
            if atr is not None and key != "payload":
                return atr
            elif key == "payload":
                return self.payload
        else:
            raise KeyError(f"{key} not found in ForeverGenerationResponse")
    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    
class ForeverGeneration(abc.ABC):
    def __init__(self, payload: dict, *args: Any, **kwargs: Any) -> None:
        self._payload = payload.copy()
        self.is_generating = False
        self._stop_event = asyncio.Event()

    @abc.abstractmethod
    async def get_payload(self) -> dict:
        raise NotImplementedError

    async def generate_forever(self, **override_payload: Any) -> AsyncGenerator[ForeverGenerationResponse, None]:
        """
        payloadを取得する関数を受け取り生成を続ける

        """
        if self.is_generating:
            error("Already generating, cannot start a new generation.")
            return

        text = ""
        self.is_generating = True
        self._stop_event.clear()
        default_payload = self._payload | override_payload
        api = Txt2imgAPI(payload=default_payload)

        try:
            while not self._stop_event.is_set() and self.is_generating:
                payload = await self.get_payload()
                async for i in api.generate_with_progress(**payload):
                    if i[0] is False:  # 終わってないなら
                        progress = i[2]
                        # println(f"[in forever_generation.py] Progress: {progress}")
                        yield ForeverGenerationResponse(
                            success="in_progress",
                            progress=progress,
                            payload=payload,
                        )
                        continue
                    elif i[0] is None:  # エラー
                        yield ForeverGenerationResponse(
                            success="error",
                            payload=payload,
                        )
                        continue
                    elif i[0] is True:  # 終わったら
                        result = i[1]
                        yield ForeverGenerationResponse(
                            success="completed",
                            result=result,
                            payload=payload,
                        )
                        break
                await asyncio.sleep(1.5)  # OSErrorを防ぐ
        except Exception as e:
            critical(f"Error generating image: {e}")
            raise
        finally:
            self.is_generating = False
            self._stop_event.set()
            print("Generation stopped.")
        return

    async def stop_generation(self) -> None:
        self._stop_event.set()
        self.is_generating = False
        println("Generation stopped by user.")

    async def start_generation(self) -> AsyncGenerator[dict, None]:
        if self.is_generating:
            error("Already generating, cannot start a new generation.")
            raise gr.Error("Already generating, cannot start a new generation.")
            
        println("Generation started.")
        async for item in self.generate_forever():
            yield item
