from utils import *
import os
import asyncio
import onnxruntime as ort

class OnnxRuntime:
  def __init__(self, model_path: str):
    # modelname.onnx
    self.model_name: str = os.path.basename(model_path)
    # models/?/modelname.onnx
    self.model_path = model_path
    self.session = None
    
  async def load_with_async(self, path, **kw):
    return await asyncio.to_thread(ort.InferenceSession, path, **kw)
  
  async def load_model(self) -> bool:
    """
    モデルをCPUにロードする
    """
    await self.unload_model()
    try:
      self.session = await self.load_with_async(self.model_path, providers=["CPUExecutionProvider"])
      return True
    except Exception as e:
      critical(f"Failed to load ONNX model from {self.model_path}: {e}")
      return False 
  
  async def load_model_cuda(self) -> bool:
    """
    モデルをCUDAにロードする
    """
    await self.unload_model()
    try:
      self.session = await self.load_with_async(self.model_path)
      return True
    except Exception as e:
      critical(f"Failed to load ONNX model with CUDA from {self.model_path}: {e}")
      return False
    
  async def unload_model(self):
    if self.session is not None:
      del self.session
      self.session = None
      println(f"Unloaded ONNX model from {self.model_path}")