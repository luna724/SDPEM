import time
import datetime
import asyncio
from utils import print_critical, AnsiColors

class InvalidTimerException(Exception):
  """タイマーが無効な場合に発生する例外
  主に end_time に関するやつ"""
  def __init__(self, name: str, message: str = "ValueError: end_time is None.") -> None:
    message = f"{AnsiColors.RED}{name}{AnsiColors.RESET}: {message}"
    print_critical(message)
    super().__init__(message)
    self.message = message

  def __str__(self) -> str:
    return self.message

class TimerInstance:
  def __init__(self, name: str = "timer", end_at: float = None) -> None:
    self.name = name
    self.start_time = time.time()
    self.end_time = end_at
  
  def __bool__(self) -> bool:
    return self.end_time is not None

  def set_end_at(self, end_at: float) -> None:
    self.end_time = end_at
  
  def end_at_dt(self, end_at: datetime.datetime) -> None:
    self.end_time = end_at.timestamp()
  
  def dtparse(self, dt: str) -> datetime.datetime:
    """webui内で使われる形式を自動変換する"""
    return datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
  
  def elapsed(self) -> float:
    if self:
      return self.end_time - self.start_time
    raise InvalidTimerException(self.name)
  
  def is_done(self) -> bool:
    if self:
      return time.time() >= self.end_time
    raise InvalidTimerException(self.name)

  def remaining(self) -> float:
    if self:
      return max(0, self.end_time - time.time())
    raise InvalidTimerException(self.name)

  def wait_for_done_blocking(self):
    if self:
      time.sleep(self.remaining())
    raise InvalidTimerException(self.name)

  async def wait_for_done(self):
    if self:
      await asyncio.sleep(self.remaining())
    raise InvalidTimerException(self.name)