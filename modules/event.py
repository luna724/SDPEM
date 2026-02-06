import asyncio
import traceback
from pydantic import BaseModel
from typing import Any, Callable, Optional, get_type_hints
import inspect

from logger import critical

class CallbackChainObject:
  def __init__(self, result: Any, sid, prv: "CallbackChainObject" = None):
    self.last_result: Any = result
    if prv is None:
      self.first_result: Any = result
      self.chains: list[str] = [sid]
    else:
      self.first_result = prv.first_result
      self.chains = prv.chains + [sid]
      del prv

class Callback:
  def __init__(
    self, cb: Callable, order: int = -1, auto_chain: bool = False,
    chain_option: dict = None, once: bool = False
  ):
    self.id = id(self)
    self.cb = cb
    self.order = order
    self.auto_chain = auto_chain
    self.chain = chain_option is not None
    self.chain_option = chain_option
    self.once = once
    
    if auto_chain and not self.chain:
      self.chain = True
      self.chain_option = {
        "mode": "any"
      }
  
  async def run(self, this: "Event", event: "EventType", chain: "CallbackChainObject" = None) -> CallbackChainObject:
    sig = get_type_hints(self.cb)
    sig.pop("return", None)
    args = [event.model_copy()]
    if len(sig) >= 2:
      args += [this, chain]
    
    try:
      if inspect.iscoroutinefunction(self.cb):
        res = await self.cb(*args)
      else:
        res = await asyncio.to_thread(self.cb, *args)
    except Exception:
      critical(f"Event Callback Error (id: {self.id})")
      traceback.print_exc()
      res = None
    if self.once:
      this.remove_callback(self.id)
    return CallbackChainObject(res, id(self), chain)

class EventType(BaseModel):
  """base class for event inputs
  このクラスを継承するものは {targetEvent}Event として命名される
  """
  event_name: str = "blank"

EventEnum = {
  -1: "blank",
  0: "generation_ended",
}


class Event:
  """base class for event/triggers
  
  各トリガーに対する基底クラス
  このクラスを継承する全てのイベントは On..の型で命名される
  """
  def __init__(self):
    self.EventId = -1
    self.accept_events: list[EventType] | Any = []
    self.target_cls = None
    
    self.callbacks: list[Callback] = []
    
    # todo: anycb
  
  def preproc(self, cb: Callback) -> Optional[Callback]: return cb
  def add_callback(self, cb: Callable, order: int = -1, chain: bool = True) -> Optional[int]:
    """return: callback id or None (not added)"""
    callback = Callback(cb, order, auto_chain=chain)
    proc_cb = self.preproc(callback)
    if proc_cb is not None:
      self.callbacks[order] = proc_cb
      return proc_cb.id
    return None
  def put_callback(self, cb: Callback) -> Optional[int]:
    """return: callback id or None (not added)"""
    proc_cb = self.preproc(cb)
    if proc_cb is not None:
      self.callbacks.append(proc_cb)
      self.callbacks = sorted(self.callbacks, key=lambda x: x.order)
      return proc_cb.id
    return None

  def remove_callback(self, cbid: int) -> bool:
    for i, cb in enumerate(self.callbacks):
      if cb.id == cbid:
        del self.callbacks[i]
        return True
    return False
  
  async def trigger(
    self, type: str, # should be Literal[..]
    obj: EventType, 
  ):
    callbacks = sorted(self.callbacks, key=lambda x: x.order)
    
    try:
      chain = await callbacks[0].run(self, obj)
      for cb in callbacks[1:]:
        if cb.chain:
          chain = await cb.run(self, obj, chain)
        else:
          await cb.run(self, obj)
    except Exception:
      critical(f"{EventEnum[self.EventId]} ({type}): Callback Error")
      traceback.print_exc()
    
  
  # @abstract
  async def auto_trig(self, *args, **kw) -> None:
    if self.target_cls is None: raise NotImplementedError("target_cls is not defined")
    