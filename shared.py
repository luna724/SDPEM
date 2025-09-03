from fastapi import FastAPI
from typing import Optional, Dict, Any
from utils import printwarn, update_enviroments
import httpx
import os

app = FastAPI()
env: Dict[str, Any] = update_enviroments()
api_path: str = env.get("api_path", "I:/stable-diffusion-webui-forge")
api_url: str = env.get("api_url", "http://localhost:7860")
pem_api: str = "http://localhost:"

pem_api_port: int = 7865
ui_port: int = 7866

session: httpx.AsyncClient = httpx.AsyncClient(
    headers={"Content-Type": "application/json"}, timeout=None
)

models: dict = {} # モデルのタイプ、名前、ファイルパスを保管する