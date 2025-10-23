import shared
import base64
import traceback
import json
import asyncio
from typing import List, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from PIL import Image
from io import BytesIO
from utils import *


class GenerationProgress(BaseModel):
    progress: float
    eta: float
    state: dict
    image: Optional[str] = None  # Base64 encoded image string

    skipped: bool = None
    interrupted: bool = None
    stopping_generation: bool = None
    step: int = None
    total_steps: int = None
    is_generating: bool = False

    async def convert_image(self) -> Optional[Image.Image]:
        """Convert base64 image string to PIL Image."""
        if self.image is None or self.image == "":
            return None
        image_data = base64.b64decode(self.image)
        try:
            return Image.open(BytesIO(image_data))
        except Image.UnidentifiedImageError:
            critical(
                f"Failed to decode image data. ({image_data[0:len(image_data)]})"
            )
            return None


class GenerationResult(BaseModel):
    raw: dict
    prompt: str
    negative: str
    seed: int
    width: int
    height: int
    sampler: str  # Euler a
    cfg_scale: float
    steps: int
    batch_size: int
    infotext: str

    images: List[str]

    async def convert_images(self) -> list[Image.Image]:
        """Convert list of base64 image strings to PIL Images."""
        return [
            Image.open(BytesIO(base64.b64decode(img)))
            for img in self.images
            if img != ""
        ]


class Txt2imgAPI:
    def __init__(self, payload: dict) -> None:
        self.payload = payload.copy()

    @staticmethod
    async def _post_requests(path: str, json: dict) -> dict:
        println(f"POST request to {path} with payload: {json}")
        response = await shared.session.post(
            url=f"{shared.api_url}{path}",
            json=json,
            headers={"Content-Type": "application/json"},
            timeout=None,
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"API request failed with status {response.status_code} ({response.text})")

    @staticmethod
    async def _get_requests(path: str, params: dict) -> dict:
        response = await shared.session.get(
            url=f"{shared.api_url}{path}",
            params=params,
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
        tuple[bool, Optional[GenerationResult], GenerationProgress], None
    ]:
        payload = self.payload | override_payload
        generation_task = asyncio.create_task(
            self._post_requests("/sdapi/v1/txt2img", payload)
        )
        try:
            while not generation_task.done():
                progress = await self.get_progress()
                # println(f"[in generate.py] Progress: {progress}")
                yield False, None, progress
                await asyncio.sleep(0.8)

            response = await generation_task
            info = json.loads(response.get("info", "{}"))
            result = GenerationResult(
                raw=info,
                prompt=info.get("prompt", ""),
                negative=info.get("negative_prompt", ""),
                seed=info.get("seed", 0),
                width=info.get("width", 0),
                height=info.get("height", 0),
                sampler=info.get("sampler_name", ""),
                cfg_scale=info.get("cfg_scale", 0.0),
                steps=info.get("steps", 0),
                batch_size=info.get("batch_size", 0),
                images=response.get("images", []),
                infotext=json.loads(response.get("info", "{}")).get("infotexts", [""])[0],
            )
            yield True, result, None
        except RuntimeError as e:
            traceback.print_exc()
            critical(f"Error generating image: {e}")
            yield None, None, None

    async def get_progress(self) -> Optional[GenerationProgress]:
        try:
            progress = await self._get_requests("/sdapi/v1/progress", {})
            cls = GenerationProgress(
                progress=progress.get("progress", 0.0) * 100,
                eta=progress.get("eta_relative", 0.0),
                state=progress.get("state", {}),
                image=progress.get("current_image", ""),
            )
            state = cls.state
            cls.skipped = state.get("skipped", False)
            cls.interrupted = state.get("interrupted", False)
            cls.stopping_generation = state.get("stopping_generation", False)
            cls.step = state.get("sampling_step", None)
            cls.total_steps = state.get("sampling_steps", None)
            cls.is_generating = state.get("job", "") != ""
        except RuntimeError as e:
            traceback.print_exc()
            critical(f"Error fetching progress: {e}")
            return None
        return cls
