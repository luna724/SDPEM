from typing import *
from modules.generate import Txt2imgAPI, GenerationProgress
from utils import *
from pydantic import BaseModel
import asyncio
import json
import traceback
from PIL import Image
import base64
import shared
from io import BytesIO


class ADetailerResult(BaseModel):
  raw: dict
  prompt: str
  negative: str
  width: int
  height: int
  images: List[str]
  
  async def convert_images(self) -> list[Image.Image]:
        """Convert list of base64 image strings to PIL Images."""
        return [
            Image.open(BytesIO(base64.b64decode(img)))
            for img in self.images
            if img != ""
        ]

class ADetailerAPI(Txt2imgAPI):
  @staticmethod
  async def _post_requests(path: str, json: dict) -> dict:
      json_for_print = json.copy()
      if "init_images" in json_for_print:
          json_for_print["init_images"] = [
              f"{len(json_for_print['init_images'])} images"
          ]
      println(f"POST request to {path} with payload: {json_for_print}")
      response = await shared.session.post(
          url=f"{shared.api_url}{path}",
          json=json,
          headers={"Content-Type": "application/json"},
          timeout=None,
      )
      if response.status_code == 200:
          return response.json()
      else:
          raise RuntimeError(f"API request failed with status {response.status_code}")
  
  async def generate_with_progress(
        self, **override_payload
    ) -> AsyncGenerator[
        tuple[bool, Optional[ADetailerResult], Optional[GenerationProgress]], None
    ]:
        payload = self.payload | override_payload
        generation_task = asyncio.create_task(
            self._post_requests("/sdapi/v1/img2img", payload)
        )
        try:
            while not generation_task.done():
                progress = await self.get_progress()
                # println(f"[in generate.py] Progress: {progress}")
                yield False, None, progress
                await asyncio.sleep(0.8)

            response = await generation_task
            info = json.loads(response.get("info", "{}"))
            result = ADetailerResult(
                raw=info,
                prompt=info.get("prompt", ""),
                negative=info.get("negative_prompt", ""),
                width=info.get("width", 0),
                height=info.get("height", 0),
                images=response.get("images", []),
            )
            yield True, result, None
        except RuntimeError as e:
            traceback.print_exc()
            critical(f"Error generating image: {e}")
            yield None, None, None