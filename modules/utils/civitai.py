# Civitai scrape helper
from httpx import AsyncClient
from typing import TypedDict

class CivitClient(AsyncClient):
  pass

class CivitResponse(TypedDict):
  

civitai = CivitClient()
async def get_civit_bs4(urls: list[str]) -> CivitResponse:
  