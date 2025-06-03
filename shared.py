from fastapi import FastAPI
import aiohttp
from typing import Optional

app = FastAPI()
api_path = "I:/stable-diffusion-webui-forge"
pem_api = "http://localhost:7865"

session: Optional[aiohttp.ClientSession] = None
def init_session():
  global session
  if session is None:
    session = aiohttp.ClientSession()