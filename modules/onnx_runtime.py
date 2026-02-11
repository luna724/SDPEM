import traceback
from typing import Literal
from utils import critical, println
from modules.utils.memory import get_current_ram_mb
from modules.config import get_config
import os
import asyncio
import torch
import onnxruntime as ort
config = get_config()

class OnnxRuntime:
  def __init__(self, model_path: str):
    # modelname.onnx
    self.model_name: str = os.path.basename(model_path)
    # models/?/modelname.onnx
    self.model_path = model_path
    self.session = None
    
    self.on_device: Literal["cpu", "cuda", "unload"] = "unload"
    self.model_size: float = -1 # MB (estimated) CUDA非対応
    
  async def load_with_async(self, path, **kw):
    return await asyncio.to_thread(ort.InferenceSession, path, **kw)
  
  async def load_model(self) -> bool:
    if config.booru_device == "cuda":
      return await self.load_model_cuda()
    else:
      return await self.load_model_cpu()
  
  async def load_model_cpu(self) -> bool:
    """
    モデルをCPUにロードする
    """
    if self.on_device == "cpu": return True
    
    await self.unload_model()
    try:
      bef = get_current_ram_mb()
      self.session = await self.load_with_async(self.model_path, providers=["CPUExecutionProvider"])
      self.on_device = "cpu"
      aft = get_current_ram_mb()
      self.model_size = max(-1, aft - bef)
      return True
    except Exception as e:
      critical(f"Failed to load ONNX model from {self.model_path}: {e}")
      return False 
  
  async def load_model_cuda(self, allow_fallback: bool = True) -> bool:
    """
    モデルをCUDAにロードする
    """
    if self.on_device == "cuda": return True
    
    await self.unload_model()
    try:
      pv = {
            "device_id": 0,
            "arena_extend_strategy": "kSameAsRequested",
            "do_copy_in_default_stream": False,
        }
      self.model_size = config.booru_cuda_inference_memory_limit
      if config.booru_cuda_inference_memory_limit >= 0:
        pv["gpu_mem_limit"] = int(config.booru_cuda_inference_memory_limit * 1024 * 1024)
      
      self.session = await self.load_with_async(self.model_path, providers=[("CUDAExecutionProvider", pv)])
      self.on_device = "cuda"
      return True
    except Exception as e:
      critical(f"Failed to load ONNX model with CUDA from {self.model_path}: {e}")
      traceback.print_exc()
      if allow_fallback:
        return await self.load_model_cpu()
      return False
    
  async def unload_model(self):
    if self.session is not None:
      del self.session
      self.session = None
      println(f"Unloaded ONNX model from {self.model_path}")
      self.on_device = "unload"