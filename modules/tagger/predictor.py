import asyncio
from typing import Optional
from utils import *
from PIL import Image
import numpy as np
import pandas as pd
from modules.onnx_runtime import OnnxRuntime
import shared
import traceback
from concurrent.futures import ThreadPoolExecutor

class OnnxRuntimeTagger(OnnxRuntime):
  @staticmethod
  def find(model_path):
    return next(
        (
            x["path"]
            for x in shared.models["wd-tagger"]
            if x["display_name"] == model_path
        ),
        model_path,
    )
  
  def __init__(self, model_path: str, find_path: bool = True):
    if find_path:
      model_path = next(
          (
              x["path"]
              for x in shared.models["wd-tagger"]
              if x["display_name"] == model_path
          ),
          model_path,
      )
    
    super().__init__(model_path)
    self.tags = []
    self.rating_indexes = []
    self.general_indexes = []
    self.character_indexes = []
    
  # async def load_model(self, *args, **kw):
  #   raise NotImplementedError("Tagger RuntimeはCUDAでのみ動作します.")
  
  def load_labels(self) -> list[str]:
    """
    {self.model_path}.selected_tags.csv のラベルを読み込む
    """
    # https://github.com/toriato/stable-diffusion-webui-wd14-tagger/blob/a9eacb1eff904552d3012babfa28b57e1d3e295c/tagger/ui.py#L368
    kaomojis = [
        "0_0",
        "(o)_(o)",
        "+_+",
        "+_-",
        "._.",
        "<o>_<o>",
        "<|>_<|>",
        "=_=",
        ">_<",
        "3_3",
        "6_9",
        ">_o",
        "@_@",
        "^_^",
        "o_o",
        "u_u",
        "x_x",
        "|_|",
        "||_||",
    ]
    df_path = os.path.join(
        os.path.dirname(self.model_path),
        os.path.splitext(os.path.basename(self.model_name))[0] + ".selected_tags.csv"
    )
    println(f"Loading labels from csv: {df_path}")
    dataframe = pd.read_csv(
      df_path
    )

    name_series = dataframe["name"]
    name_series = name_series.map(
        lambda x: x.replace("_", " ") if x not in kaomojis else x
    )
    tag_names = name_series.tolist()

    rating_indexes = list(np.where(dataframe["category"] == 9)[0])
    general_indexes = list(np.where(dataframe["category"] == 0)[0])
    character_indexes = list(np.where(dataframe["category"] == 4)[0])
    return tag_names, rating_indexes, general_indexes, character_indexes # type: ignore
  
  def load_label(self):
    tags = self.load_labels()
    self.tags = tags[0]
    self.rating_indexes = tags[1]
    self.general_indexes = tags[2]
    self.character_indexes = tags[3]
    println(f"Loaded label {self.model_name} with {len(self.tags)} tags.")
    
  async def load_model_cpu(self) -> bool:
    self.load_label()
    return await super().load_model_cpu()
  
  async def load_model_cuda(self, allow_fallback: bool = True) -> bool:
    self.load_label()
    return await super().load_model_cuda(allow_fallback=allow_fallback)
  
  def get_model_size(self) -> int:
    """モデル内にある height の値を返す"""
    if self.session is None:
      raise RuntimeError("Model is not loaded. Please load the model before getting size.")
    input_shape = self.session.get_inputs()[0].shape
    if len(input_shape) == 4:
      return input_shape[2]  # Assuming NHWC format
    elif len(input_shape) == 3:
      return input_shape[1]  # Assuming NCHW format
    else:
      raise ValueError(f"Unexpected input shape: {input_shape} (model: {self.model_name})")
    
  def prepare_image(self, image: Image.Image) -> np.ndarray:
    """
    画像をndarrayに変換し、モデルの入力サイズに合わせてリサイズする
    """
    # https://huggingface.co/spaces/SmilingWolf/wd-tagger
    target_size = self.get_model_size()

    canvas = Image.new("RGBA", image.size, (255, 255, 255))
    canvas.alpha_composite(image)
    image = canvas.convert("RGB")

    # Pad image to square
    image_shape = image.size
    max_dim = max(image_shape)
    pad_left = (max_dim - image_shape[0]) // 2
    pad_top = (max_dim - image_shape[1]) // 2

    padded_image = Image.new("RGB", (max_dim, max_dim), (255, 255, 255))
    padded_image.paste(image, (pad_left, pad_top))

    # Resize
    if max_dim != target_size:
        padded_image = padded_image.resize(
            (target_size, target_size),
            Image.Resampling.BICUBIC,
        )

    # Convert to numpy array
    image_array = np.asarray(padded_image, dtype=np.float32)

    # Convert PIL-native RGB to BGR
    image_array = image_array[:, :, ::-1]

    return np.expand_dims(image_array, axis=0)
  
  async def _predict(self, output_names: list[str], inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
    return await asyncio.to_thread(
      self.session.run, output_names, inputs # type: ignore
    ) # type: ignore
  
  def predict_sync(self, img, threshold, character_threshold):
    if self.session is None:
      raise RuntimeError("Model is not loaded. Please load the model before predicting.")
    image: np.ndarray = self.prepare_image(img)
    input_name = self.session.get_inputs()[0].name
    label_name = self.session.get_outputs()[0].name
    preds = self.session.run([label_name], {input_name: image})[0]
    
    # {"tag": threshold, ..}
    labels = list(zip(self.tags, preds[0].astype(float)))
    
    # First 4 labels are actually ratings: pick one with argmax
    ratings_names = [labels[i] for i in self.rating_indexes] # type: ignore
    character_names = [labels[i] for i in self.character_indexes] # type: ignore
    rating = dict(ratings_names)

    # Then we have general tags: pick any where prediction confidence > threshold
    general_names = [labels[i] for i in self.general_indexes] # type: ignore

    # タグ結合
    general_res = [x for x in general_names if x[1] > threshold]
    general_res = dict(general_res)
    character_res = [x for x in character_names if x[1] > character_threshold]
    character_res = dict(character_res)
    
    return (
      general_res,
      character_res,
      rating,
    ) # type: ignore
  
  async def predict(
    self, img: Image.Image, threshold: float, character_threshold: float,
    automatic_model_management: bool = False
  ) -> tuple[dict, dict, dict]:
    # https://huggingface.co/spaces/SmilingWolf/wd-tagger
    """general_res, character_res, rating を返す
    すべて tag: threshold の辞書"""
    mcut_enable = False
    character_mcut_enable = False
    
    if automatic_model_management:
      await self.load_model()
    if self.session is None:
      raise RuntimeError("Model is not loaded. Please load the model before predicting.")
    image: np.ndarray = self.prepare_image(img)
    input_name = self.session.get_inputs()[0].name
    label_name = self.session.get_outputs()[0].name
    preds = (await self._predict([label_name], {input_name: image}))[0]
    if automatic_model_management:
      await self.unload_model()
    
    # {"tag": threshold, ..}
    labels = list(zip(self.tags, preds[0].astype(float)))
    
    # First 4 labels are actually ratings: pick one with argmax
    ratings_names = [labels[i] for i in self.rating_indexes] # type: ignore
    character_names = [labels[i] for i in self.character_indexes] # type: ignore
    rating = dict(ratings_names)

    # Then we have general tags: pick any where prediction confidence > threshold
    general_names = [labels[i] for i in self.general_indexes] # type: ignore

    # タグ結合
    general_res = [x for x in general_names if x[1] > threshold]
    general_res = dict(general_res)
    character_res = [x for x in character_names if x[1] > character_threshold]
    character_res = dict(character_res)
    
    return (
      general_res,
      character_res,
      rating,
    ) # type: ignore

class OnnxTaggerMulti(OnnxRuntimeTagger):
  def __init__(self, model_name: str):
    super().__init__(model_name)
  
  async def exc(self, task, inputs, c:int=None):
    if c is None: c = max(1, os.cpu_count() - 2)
    
    def _execute_batch():
      with ThreadPoolExecutor(max_workers=c) as pool:
        return list(pool.map(task, inputs))
    
    return await asyncio.to_thread(_execute_batch)
  
  async def load_model_cuda(self, allow_fallback: bool = True) -> bool:
    if self.on_device == "cuda": return True
    await self.unload_model()
    try:
      self.session = await self.load_with_async(
      self.model_path, providers=[("CUDAExecutionProvider", {
          "device_id": 0,
          "arena_extend_strategy": "kSameAsRequested",
          "do_copy_in_default_stream": False,
      })]
    )
      self.on_device = "cuda"
    except Exception as e:
      traceback.print_exc()
      self.on_device = "unload"
      return False
    return True
  
  async def predict(
    self, img: list[Image.Image], threshold: float, character_threshold: float, c: int = None,
    automatic_model_management: bool = True
  ) -> list[tuple[dict, dict, dict]]:
    if automatic_model_management:
      await self.load_model()
    if self.session is None:
      raise RuntimeError("Model is not loaded. Please load the model before predicting.")
    if c is None: c = max(1, os.cpu_count() - 2)
    
    input_name = self.session.get_inputs()[0].name
    label_name = self.session.get_outputs()[0].name
    images: list[np.ndarray] = await self.exc(self.prepare_image, img, c)
    s = self.session
    
    def worker(img):
      try:
        iob = s.io_binding
        iob.bind_cpu_input(input_name, img)
        iob.bind_output(label_name, device_type="cuda")
        s.run_with_iob(iob)
        return iob.copy_outputs_to_cpu()[0]
      except Exception as e:
        return traceback.format_exc()
    
    preds_all = await self.exc(worker, images, c)
    
    if automatic_model_management:
      await self.unload_model()
    
    def format_tags(preds):
      labels = list(zip(self.tags, preds[0].astype(float)))
      
      # First 4 labels are actually ratings: pick one with argmax
      ratings_names = [labels[i] for i in self.rating_indexes] # type: ignore
      character_names = [labels[i] for i in self.character_indexes] # type: ignore
      rating = dict(ratings_names)

      # Then we have general tags: pick any where prediction confidence > threshold
      general_names = [labels[i] for i in self.general_indexes] # type: ignore

      # タグ結合
      general_res = [x for x in general_names if x[1] > threshold]
      general_res = dict(general_res)
      character_res = [x for x in character_names if x[1] > character_threshold]
      character_res = dict(character_res)
      
      return (
        general_res,
        character_res,
        rating,
      ) # type: ignore
    
    return await self.exc(format_tags, preds_all, c*10)

sharedRuntime: Optional[OnnxRuntimeTagger] = None
def auto_init_sharedRuntime():
  global sharedRuntime
  if sharedRuntime is None:
    sharedRuntime = OnnxRuntimeTagger(shared.models["wd-tagger"][0]["display_name"])
    # await sharedRuntime.load_model()