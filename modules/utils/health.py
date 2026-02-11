import httpx
import asyncio
import traceback
from httpx import AsyncClient
from typing import Optional
from logger import error
from modules.config import get_config
config = get_config()

class HealthChecker:
  def __init__(self, url, check_path: str = "/docs"):
    self.alive: Optional[bool] = None
    self.url: str = url
    self.check_path = check_path
    
    self.client: AsyncClient = AsyncClient()
  
  async def checker(
    self, interval = 60
  ):
    while True:
      try:
        rsp = await self.client.get(
          self.url + self.check_path,
          follow_redirects=True
        )
        rsp.raise_for_status()
        self.alive = True
      
      except httpx.HTTPStatusError as e:
        self.alive = False
        error(f"[HealthCheck]: failed with status: {e.response.status_code}")
        
      except Exception as e:
        self.alive = False
        error(f"[HealthCheck]: unknown error")
        traceback.print_exc()
        
      await asyncio.sleep(interval)

  @property
  def is_alive(self) -> bool:
    return self.alive is True


a1111: HealthChecker = HealthChecker(config.a1111_url + config.api_path, config.a1111_health_check_path)