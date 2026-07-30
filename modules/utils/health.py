import httpx
import asyncio
from httpx import AsyncClient
from modules.config import get_config
config = get_config()

class HealthChecker:
  def __init__(self, url: str, check_path: str = "/docs"):
    self.alive: bool | None = None
    self.url: str = url
    self.check_path = check_path
    
    self.client: AsyncClient = AsyncClient()
  
  async def checker(
    self, interval: int = 60
  ):
    while True:
      try:
        rsp = await self.client.get(
          self.url + self.check_path,
          follow_redirects=True
        )
        self.alive = (rsp.status_code == 200)
      except Exception:
        self.alive = False
        
      await asyncio.sleep(interval)

  @property
  def is_alive(self) -> bool:
    return self.alive is True


a1111: HealthChecker = HealthChecker(config.a1111_url, config.a1111_health_check_path)