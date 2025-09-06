import asyncio
from typing import Coroutine
from utils import *

class StateManagerException(Exception): pass
class StateManager:
    def __init__(self, instance, proc_name: str = "Test StateManager"):
        self.instance = instance # 元インスタンス
        self.proc_name: str = proc_name
        self.opts = {}
        self.taken_by: str = "?"
        self.log: str = ""
        
        self.vars = {}
        self._shutdown_flag = False
    def killed(self) -> bool: return self._shutdown_flag is True
        
    def kill(self, reason: str):
        """Terminate Process ANYWAY (unsafe)"""
        if reason != "__Root_Shutdown__":
            critical(f"Task ({self.proc_name}) Killed by StateManager: {reason}")
        self._shutdown_flag = True
        
    def on_root_shutdown(self): 
        """実行元クラスから呼び出されるシャットダウン処理"""
        self.kill("__Root_Shutdown__")
        self.cleanup()
        
    def shutdown(self) -> Any:
        """実行元クラスを安全に終了したい際に使う
        return: 終了処理の結果 (インスタンスから返ってくるやつ)
        """
        if not (
            hasattr(self.instance, "killable") and
            callable(self.instance.stop) and
            isinstance(self.instance.stop, function)
        ): raise StateManagerException(f"{self.proc_name} Invalid instance methods")
        killable = self.instance.killable
        
        if killable:
            hasattr(self.instance, "stop")
            coro = self.instance.stop()
            if isinstance(coro, Coroutine):
                r = asyncio.run_coroutine_threadsafe(
                    coro, asyncio.get_event_loop()
                ).result()
            else:
                r = coro
        else:
            if hasattr(self.instance, "killMethod"):
                fn = getattr(
                    self.instance, self.instance.killMethod
                )
                coro = fn(self)
            elif hasattr(self.instance, "stop"):
                coro = self.instance.stop()
            else:
                raise StateManagerException(f"Instance {self.proc_name} has no valid stop method")

            if isinstance(coro, Coroutine):
                r = asyncio.run_coroutine_threadsafe(
                    coro, asyncio.get_event_loop()
                ).result()
            else:
                r = coro
        
        self.on_root_shutdown()
        return r
    
    def cleanup(self):
        pass # TODO

    def get(
        self, k: str, default=None
    ):
        return self.vars.get(k, default)
    
    def get_option(
        self, k: str, default=None
    ):
        return self.opts.get(k, default)
    
    