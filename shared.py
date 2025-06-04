from fastapi import FastAPI
from typing import Optional
from utils import printwarn
import httpx

app = FastAPI()
api_path = "I:/stable-diffusion-webui-forge"
api_url = "http://localhost:7860"
pem_api = "http://localhost:7865"

session: httpx.AsyncClient = httpx.AsyncClient(headers={"Content-Type": "application/json"}, timeout=None)