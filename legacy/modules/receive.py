import base64
import io
from io import BytesIO

from PIL import Image
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import shared
from modules.image_progress import ImageProgressAPI


class onSave(BaseModel):
    infotxt: str
    image: str


def initialize_server():
    app = FastAPI()
    shared.app = app

    @app.get("/")
    async def alive():
        return JSONResponse(
            content={"status": "ok"}, status_code=200
        )

    @app.post("/on_save")
    async def on_save(data: onSave):
        try:
            image = Image.open(io.BytesIO(base64.b64decode(data.image.encode())))

            ImageProgressAPI.last_generated_image = image
            ImageProgressAPI.last_image = image
            ImageProgressAPI.last_generated_info = data.infotxt
            ImageProgressAPI.last_info = data.infotxt

            print(f"[Server]: Received data from sdwebui/extension!")
            return JSONResponse(
                content={"status": "ok"}, status_code=200
            )

        except Exception as e:
            print(f"[Server]: failed receive data from sdwebui/extension: {e}")
            return JSONResponse(
                content={"status": str(e)}, status_code=500
            )