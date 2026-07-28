import asyncio
import cv2
import numpy as np
from modules.onnx_runtime import OnnxRuntime

class AsyncAnimeSegmentation:
  def __init__(self, model_path="models/anime-seg/isnetis.onnx"):
    self.ort = OnnxRuntime(model_path)
    self.model_path = model_path

  async def load_model(self):
    await self.ort.load_model()

  async def get_mask(self, input_img, s=1024):
    """
    非同期でマスクを推論する
    """
    if self.ort.session is None:
      raise ValueError("Model is not loaded.")
    
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, self._get_mask_sync, input_img, s)

  def _get_mask_sync(self, input_img, s=1024):
    input_img = (input_img / 255).astype(np.float32)
    h0, w0 = input_img.shape[:-1]
    h, w = (s, int(s * w0 / h0)) if h0 > w0 else (int(s * h0 / w0), s)
    ph, pw = s - h, s - w
    img_input = np.zeros([s, s, 3], dtype=np.float32)
    img_input[ph // 2:ph // 2 + h, pw // 2:pw // 2 + w] = cv2.resize(input_img, (w, h))
    img_input = np.transpose(img_input, (2, 0, 1))
    img_input = img_input[np.newaxis, :]
    
    input_name = self.ort.session.get_inputs()[0].name
    pred = self.ort.session.run(None, {input_name: img_input})[0][0]
    
    pred = np.transpose(pred, (1, 2, 0))
    pred = pred[ph // 2:ph // 2 + h, pw // 2:pw // 2 + w]
    pred = cv2.resize(pred, (w0, h0))[:, :, np.newaxis]
    return pred

  async def segment_image(self, img, s=1024, only_matted=False, bg_white=False):
    """
    画像を切り抜き用途に合わせて合成する非同期メソッド
    """
    mask = await self.get_mask(img, s=s)
    
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, self._process_image_sync, img, mask, only_matted, bg_white)

  def _process_image_sync(self, img, mask, only_matted=False, bg_white=False):
    if only_matted and bg_white:
      result = np.concatenate((mask * img + 255 * (1 - mask), mask * 255), axis=2).astype(np.uint8)
      result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    elif only_matted:
      result = np.concatenate((mask * img + 1 - mask, mask * 255), axis=2).astype(np.uint8)
      result = cv2.cvtColor(result, cv2.COLOR_RGBA2BGRA)
    else:
      result = np.concatenate((img, mask * img, mask.repeat(3, 2) * 255), axis=1).astype(np.uint8)
      result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    return result

isnetis_seg = None

def get_anime_seg():
  global isnetis_seg
  if isnetis_seg is None:
    isnetis_seg = AsyncAnimeSegmentation()
  return isnetis_seg