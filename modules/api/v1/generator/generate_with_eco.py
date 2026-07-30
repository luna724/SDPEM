import base64
import json
import os
from io import BytesIO
from pydantic import BaseModel
from shared import app
from typing import Optional
from fastapi import status
from fastapi.responses import JSONResponse
from PIL import Image
from modules.generate import Txt2imgAPI
from modules.forever.common import ForeverGenerationTemplate

DEFAULT_ECO_CONFIG = {
  "negative": "",
  "batch_size": 1,
  "batch_count": 1,
  "adetailer": False,
  "enable_hand_tap": False,
  "disable_lora_in_adetailer": False,
  "enable_freeu": False,
  "freeu_preset": "SDXL",
  "freeu_b1": 1.3,
  "freeu_b2": 1.4,
  "freeu_s1": 0.9,
  "freeu_s2": 0.2,
  "freeu_start": 0.0,
  "freeu_stop": 1.0,
  "enable_neveroom_unet": False,
  "enable_neveroom_vae": False,
  "enable_sag": False,
  "sag_scale_min": 0.0,
  "sag_scale_max": 0.55,
  "enable_pag": False,
  "pag_scale_min": 0.0,
  "pag_scale_max": 3.0,
  "pag_attn_min": 0.0,
  "pag_attn_max": 0.0,
  "pag_start": 0.0,
  "pag_stop": 1.0,
  "enable_apg": False,
  "apg_eta": 0.0,
  "apg_rescale_min": 0.0,
  "apg_rescale_max": 12.0,
  "icg_scale_min": 0.0,
  "icg_scale_max": 0.0,
  "icg_start": 0.4,
  "apg_momentum": -0.5,
  "post_cfg_method": "None",
  "enable_ld": False,
  "ld_method": "(SDXL) Only Generate Transparent Image (Attention Injection)",
  "ld_weight": 1.0,
  "ld_stop": 1.0,
  "ld_img_resize": "Crop and Resize",
  "ld_fore_back_ground": "",
  "ld_blend": "",
  "enable_sa": False,
  "sa_share_attn": False,
  "sa_str": 0.5,
  "enable_lm": False,
  "lms_multiplier": 1.0,
  "lms_method": "multiply",
  "lmt_multiplier": 1.0,
  "lmt_method": "multiply",
  "lmt_p": 0.5,
  "lm_contrast": 1.0,
  "lmc_method": "multiply",
  "lmc_drift": 0.0,
  "lm_cfg_phi": 1.0,
  "lme_multiplier": 1.0,
  "lme_lowpass": 0.5,
  "lmn_size": 1,
  "lmn_multiplier": 1.0,
  "lmm_mode": "multiply",
  "lmm_p": 0.5,
  "lmm_multiplier": 1.0,
  "lm_uncond": False,
  "lm_dyn_cfg": False,
  "enable_hrfx": False,
  "hrfx_block": "Input",
  "hrfx_downscale": 2.0,
  "hrfx_start": 0.0,
  "hrfx_stop": 1.0,
  "hrfx_dmethod": "bicubic",
  "hrfx_umethod": "bicubic",
  "hrfx_downscale_skipped": 0,
  "hr_i2i_mode": "None",
  "hr_scale": 2.0,
  "hr_w": 0,
  "hr_h": 0,
  "hr_step": 20,
  "hr_upscaler": "Latent",
  "hr_scaler_method": "Scale by",
  "hr_prompt": "",
  "hr_negative": "",
  "hr_denoise": 0.7,
  "hr_sampler": "Euler a",
  "hr_cfg": 7.0,
  "hr_scheduler": "Automatic",
  "enable_refiner": False,
  "refiner_cp": "",
  "refiner_swap_at": 0.8,
  "enable_hr": False,
  "merge_adetailer_test": False,
  "adetailer_sep_param_test": None,
  "is_flux": False,
  "enable_auto_stop": True,
  "stop_mode": "After Images",
  "stop_minutes": 10,
  "stop_after_img": 1,
  "stop_after_datetime": "",
  "s_method": ["Euler a"],
  "scheduler": ["Automatic"],
  "steps_min": 20,
  "steps_max": 20,
  "cfg_min": 7.0,
  "cfg_max": 7.0,
  "size": "896:1152",
  "ad_step_multiplier": 0.5,
  "save_tmp_images": False,
  "prompt_generation_max_tries": 500,
  "header": "",
  "footer": "",
  "tags": 7,
  "random_rate": 1.0,
  "prompt_weight_chance": 0.05,
  "prompt_weight_min": 0.5,
  "prompt_weight_max": 1.5,
  "remove_character": False,
  "booru_filter_enable": False,
  "instance_blacklist": "",
  "booru_model": "wd14-v2",
  "booru_use_shared": True,
  "output_dir": "./output/{DATE}",
  "output_format": "PNG",
  "output_name": "{seed}",
  "save_metadata": True,
  "save_infotext": True
}

def get_default_config() -> dict:
  config = DEFAULT_ECO_CONFIG.copy()
  try:
    from modules.utils.ui.register import RegisterComponent
    rc = RegisterComponent.get_rc("forever_generation/from_lora")
    current_preset = rc.pmgr.current_preset
    
    # Try loading from pmgr (which handles RAM cache and disk)
    preset_data = rc.pmgr.load(current_preset)
    if preset_data:
      config.update(preset_data)
  except Exception:
    # Fallback to direct disk read if RegisterComponent fails
    try:
      config_path = "config/presets/forever_generation.from_lora/default.json"
      if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
          preset_data = json.load(f)
          if preset_data:
            config.update(preset_data)
    except Exception as e:
      print(f"Failed to load eco config: {e}")
  return config

class GenerateWithEcoRequest(BaseModel):
  prompt: str
  negative: str = ""
  header: str = ""
  footer: str = ""
  iter: int = 1
  batch: int = 1
  alwayson: dict = {}
  enable_neveroom_unet: bool = False
  enable_neveroom_vae: bool = False

@app.post("/v1/generator/generate_with_eco")
async def generate_with_eco(rq: GenerateWithEcoRequest):
  """
  config/より最新のeco設定を取得し、設定のみを再利用して画像生成を行うAPI
  """
  kw = get_default_config()
  
  # prompt, negativeは後で結合するためここでは上書きしない (重複を防止)
  # ただし、エコシステムのheader, footerは無視し、リクエストの指定（デフォルト空文字）を使用する
  kw.update({
    "header": rq.header,
    "footer": rq.footer,
    "batch_count": rq.iter,
    "batch_size": rq.batch,
    "enable_neveroom_unet": rq.enable_neveroom_unet,
    "enable_neveroom_vae": rq.enable_neveroom_vae,
    "stop_mode": "After Images",
    "enable_auto_stop": True,
    "stop_after_img": rq.batch * rq.iter,
  })

  gen = ForeverGenerationTemplate()
  
  # 設定のみを再利用 (prepare_param, update_prompt_settings)
  await gen.prepare_param(**kw)
  await gen.update_prompt_settings(**kw)
  
  # ペイロードの構築
  payload = await gen._get_payload()
  
  # header/footerとリクエストのpromptを結合
  payload["prompt"] = gen.combine_header_footer(rq.prompt)
  
  # negative promptの結合
  eco_neg = payload.get("negative_prompt", "").strip(", ")
  if rq.negative:
    if eco_neg:
      payload["negative_prompt"] = f"{eco_neg}, {rq.negative}"
    else:
      payload["negative_prompt"] = rq.negative

  if rq.alwayson:
    payload["alwayson_scripts"].update(rq.alwayson)

  # 生成処理 (Txt2imgAPIを利用し、forever/common.pyの無限ループ等の機構は利用しない)
  api = Txt2imgAPI(payload=payload)
  collected_images: list[Image.Image] = []
  
  try:
    async for i in api.generate_with_progress():
      if i[0] is True:  # 完了
        result = i[1]
        if result and result.images:
          collected_images = await result.convert_images()
        break
      elif i[0] is None:  # エラー
        raise Exception("Image generation failed")
  except Exception as e:
    return JSONResponse(
      {"success": False, "message": str(e)},
      status.HTTP_500_INTERNAL_SERVER_ERROR,
      media_type="application/json"
    )

  if not collected_images:
    return JSONResponse(
      {"success": False, "message": "No images were generated"},
      status.HTTP_500_INTERNAL_SERVER_ERROR,
      media_type="application/json"
    )

  images_b64 = []
  for img in collected_images:
    buf = BytesIO()
    img.save(buf, format="PNG")
    images_b64.append(base64.b64encode(buf.getvalue()).decode("utf-8"))

  return JSONResponse(
    {
      "success": True,
      "images": images_b64
    },
    status.HTTP_200_OK,
    media_type="application/json"
  )
