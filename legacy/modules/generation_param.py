import os

from pydantic import BaseModel

from jsonutil import JsonUtilities
from modules.api_helper import p

class Params(BaseModel):
    """/sdapi/v1/txt2img のためのパラメータを pydantic にて提供します"""
    prompt: p = p("", str, "")
    negative_prompt: p = p("", str, "")
    styles: p = p([], list, [])
    seed: p = p(-1, int, -1)
    subseed: p = p(-1, int, -1)
    subseed_strength: p = p(0.0, float, 0.0)
    seed_resize_from_h: p = p(-1, int, -1)
    seed_resize_from_w: p = p(-1, int, -1)
    sampler_name: p = p("Euler a", str, "Euler a")
    scheduler: p = p("Automatic", str, "Automatic")
    batch_size: p = p(1, int, 1)
    n_inter: p = p(1, int, 1)
    steps: p = p(50, int, 50)
    cfg_scale: p = p(7.0, float, 7.0)
    width: p = p(512, int, 512)
    height: p = p(512, int, 512)
    restore_faces: p = p(False, bool, False)
    tiling: p = p(False, bool, False)
    do_not_save_samples: p = p(False, bool, False)
    do_not_save_grid: p = p(False, bool, False)
    eta: p = p(0, int, 0)
    denoising_strength: p = p(0.0, float, 0.0)
    s_min_uncond: p = p(0, int, 0, dataclass=True)
    s_churn: p = p(0, int, 0, dataclass=True)
    s_tmax: p = p(0, int, 0, dataclass=True)
    s_tmin: p = p(0, int, 0, dataclass=True)
    s_noise: p = p(0, int, 0, dataclass=True)
    override_settings: p = p({}, dict, {}, allow_invalidate=True)
    override_settings_restore_afterwards: p = p(True, bool, True)
    refiner_checkpoint: p = p("", str, "")
    refiner_switch_at: p = p(0.0, float, 0.0)
    disable_extra_networks: p = p(False, bool, False)
    firstpass_image: p = p("", str, "")
    comments: p = p({}, dict, {}, allow_invalidate=True)
    enable_hr: p = p(False, bool, False)
    firstphase_width: p = p(0, int, 0)
    firstphase_height: p = p(0, int, 0)
    hr_scale: p = p(2.0, float, 2.0)
    hr_upscaler: p = p("R-ESRGAN 4x+ Anime6B", str, "R-ESRGAN 4x+ Anime6B")
    hr_second_pass_steps: p = p(0, int, 0)
    hr_resize_x: p = p(0, int, 0)
    hr_resize_y: p = p(0, int, 0)
    hr_checkpoint_name: p = p("", str, "")
    hr_sampler_name: p = p("", str, "")
    hr_scheduler: p = p("", str, "")
    hr_prompt: p = p("", str, "")
    hr_negative_prompt: p = p("", str, "")
    force_task_id: p = p("", str, "")
    sampler_index: p = p("Euler", str, "Euler")
    script_name: p = p("", str, "")
    script_args: p = p([], list, [])
    send_images: p = p(True, bool, True)
    save_images: p = p(False, bool, False)
    alwayson_scripts: p = p({}, dict, {}, allow_invalidate=True)
    infotext: p = p("", str, "")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, parameters):
        super().__init__(**parameters)

class GenerationParameter:
    """
    生成パラメータに関する物をパッケージ化するクラス
    """
    def __init__(self):
        self.params = Params({})

    def set_params(self, parameters: dict):
        for k, v in parameters.items():
            if hasattr(self.params, k):
                setattr(self.params, k, v)

    def get_params(self):
        return self.params.model_dump()

    def get_param(self, key: str):
        return getattr(self.params, key, None)

def get_generation_param():
    return JsonUtilities(os.path.join(os.getcwd(), "configs/default/gen_param.json")).make_dynamic_data()

# WebUI 用、デフォルトパラメータをリアルタイムでwebUIからすべての推論スクリプト向けの引数を設定する
import gradio as gr
class GenerationParameterDefault(GenerationParameter):
    """
    Deprecated.
    use JsonUtilities("configs/default/gen_param.json").make_dynamic_data()

    """
    def __init__(self):
        super().__init__()
        self.elements = {}

    def register(self, element: gr.components.Component):
        if (
            isinstance(element, gr.Textbox) or
            isinstance(element, gr.Slider) or
            isinstance(element, gr.Dropdown) or
            isinstance(element, gr.Checkbox) or
            isinstance(element, gr.Number) or
            isinstance(element, gr.Radio)
        ):
            self.elements[element.elem_id] = element
        else:
            print(f"[ERROR]: Unknown element type ({type(element)})")

        return element