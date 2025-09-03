from modules.tagger import predictor
from utils import *
from typing import *
from fastapi import File, UploadFile, status
from pydantic import BaseModel
from shared import app
from PIL import Image
from io import BytesIO
import base64

instance: predictor.OnnxRuntimeTagger = None
class _LoadModelRequest(BaseModel):
  model_path: str
  find_path: bool = True

@app.post("/v1/wd_tagger/load")
async def load_model(request: _LoadModelRequest):
  global instance
  if instance is not None:
    await instance.unload_model()
    del instance
  instance = predictor.OnnxRuntimeTagger(request.model_path, request.find_path)
  if instance is None:
    return {"success": False, "message": "Model not found"}, status.HTTP_400_BAD_REQUEST
  if not await instance.load_model_cuda():
    del instance
    instance = None
    return {"success": False, "message": "Failed to load model on CUDA."}, status.HTTP_500_INTERNAL_SERVER_ERROR
  else:
    return {"success": True, "message": ""}, status.HTTP_200_OK
  

@app.post("/v1/wd_tagger/unload")
async def unload_model():
  global instance
  if instance is not None:
    await instance.unload_model()
    del instance
  return {"success": True, "message": ""}, status.HTTP_200_OK


class _PredictRequest(BaseModel):
  image: str # base64 encoded image
  threshold: float = 0.5
  character_threshold: float = 0.5
@app.post("/v1/wd_tagger/predict")
async def predict(request: _PredictRequest):
  global instance
  if instance is None:
    return {"success": False, "message": "Model not loaded"}, status.HTTP_501_NOT_IMPLEMENTED
  try:
    img = Image.open(BytesIO(base64.b64decode(request.image)))
    if img.mode != 'RGBA':
      img = img.convert('RGBA')
  except Exception as e:
    return {"success": False, "message": f"Invalid image: {str(e)}"}, status.HTTP_400_BAD_REQUEST
  result = await instance.predict(img, request.threshold, request.character_threshold)
  return {"success": True, "result": result}, status.HTTP_200_OK