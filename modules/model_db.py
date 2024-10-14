from lunapy_module_importer import Importable, Importer
from typing import *

class model_db:
  def __init__(self, isPEM:bool=True):
    # isPEM が True ならモデルを手動で設定する
    # False なら UI のほかデータに基づきモデルを取得しようとする
    if isPEM:
      self.adetailer_models:List[str] = [
        "face_yolov8n.pt",
        "face_yolov8s.pt",
        "hand_yolov8n.pt",
        "person_yolov8n-seg.pt",
        "person_yolov8s-seg.pt",
        "yolov8x-worldv2.pt",
        "mediapipe_face_full",
        "mediapipe_face_short",
        "mediapipe_face_mesh",
        "mediapipe_face_mesh_eyes_only"
      ]

    self.get_config = Importer("modules.config.get").get_spec_value
    primary_models = self.get_config("system.save.model_info.primary_model")
  
  def get_adetailer_models(self) -> List[str]:
    return self.adetailer_models
  
  def get_adetailer_primary_model(self) -> str:
    return self.primary_models["ADetailer"]
  
  
  
class mdb(Importable):
  def __call__(self, **kwarg):
    return model_db(kwarg["isPEM"])
  
  