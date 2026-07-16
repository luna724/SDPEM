from typing import TYPE_CHECKING
if TYPE_CHECKING:
  
from modules import scripts
from modules.processing import StableDiffusionProcessing, StableDiffusionProcessingImg2Img
from modules.paths import models_path
from backend import utils, memory_management

class SDPEM(scripts.Script):
    def __init__(self):
        self._components = []
  
    def title(self):
        return "SDPEM"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        return None

    def after_component(self, component, **kwargs):
        