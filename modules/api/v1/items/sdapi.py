from pydantic import BaseModel
from shared import app, api_url
import shared
from typing import *
from fastapi import status
from utils import *

async def get(path: str) -> Any:
  response = await shared.session.get(
    url=api_url + path,
    headers={"Content-Type": "application/json"}
  )
  if response.status_code == status.HTTP_200_OK:
    data = response.json()
    return data
  else:
    return {"success": False, "message": f"Failed to retrieve data ({response.status_code})"}, status.HTTP_500_INTERNAL_SERVER_ERROR

@app.get("/v1/items/sdapi/samplers")
async def get_samplers() -> tuple[list[str], int]:
  unresized = await get("/sdapi/v1/samplers")
  return [
    x["name"] for x in unresized if "name" in x
  ], status.HTTP_200_OK

@app.get("/v1/items/sdapi/schedulers")
async def get_schedulers() -> tuple[list[str], int]:
  unresized = await get("/sdapi/v1/schedulers")
  return [
    x["label"] for x in unresized if "label" in x
  ], status.HTTP_200_OK

@app.get("/v1/items/sdapi/sd_models")
async def get_sd_models() -> tuple[list[str], int]:
  unresized = await get("/sdapi/v1/sd-models")
  return [
    x["model_name"] for x in unresized if "model_name" in x
  ], status.HTTP_200_OK