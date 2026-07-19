from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import json
from PIL import Image
import numpy as np
import cv2
import asyncio

from modules.anime_seg import AsyncAnimeSegmentation
from modules.tagger.predictor import auto_init_sharedRuntime, sharedRuntime

class PngInfo(UiTabs):
  def title(self) -> str:
    return "Segmentation"
  def index(self) -> int:
    return 6
  def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
    with gr.Column():
      input_img = gr.Image(label="input image", type="numpy")
      run_btn = gr.Button(variant="primary")
    with gr.Row():
      output_mask = gr.Image(label="mask", format="png", type="numpy")
      output_img = gr.Image(label="result", image_mode="RGBA", format="png", type="numpy")

    with gr.Accordion("Adv.", open=True):
      with gr.Row():
        twoway_filter = gr.Textbox(label="Two-way filter (tag)", placeholder="e.g. anime, 1girl, solo", lines=1, value="")
        twoway_mode = gr.Radio(label="Two-way mode", choices=["AND", "OR"], value="AND", type="value")
      crop_output = gr.Checkbox(label="Crop output", value=False)
        
      run_btn.click(self.rmbg_fn, [input_img, twoway_filter, twoway_mode, crop_output], [output_mask, output_img])

  async def rmbg_fn(self, img: np.ndarray, tags: str, mode: str, crop: bool):
    if img is None:
      return None, None
      
    seg = AsyncAnimeSegmentation()
    await seg.load_model()
    
    mask = await seg.get_mask(img)
    # mask is (H, W, 1) float32 [0, 1]
    
    target_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]
    
    if target_tags:
      auto_init_sharedRuntime()
      await sharedRuntime.load_model()
      
      mask_uint8 = (mask[:, :, 0] * 255).astype(np.uint8)
      _, binary_mask = cv2.threshold(mask_uint8, 127, 255, cv2.THRESH_BINARY)
      num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
      
      final_mask = np.zeros_like(mask_uint8)
      
      for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 100:
          continue
            
        comp_mask = (labels == i).astype(np.uint8)
        
        x, y, w, h, _ = stats[i]
        comp_img_np = img[y:y+h, x:x+w].copy()
        comp_mask_cropped = comp_mask[y:y+h, x:x+w]
        
        # Apply mask to cropped image
        comp_img_rgba = np.concatenate((comp_img_np, comp_mask_cropped[:, :, np.newaxis] * 255), axis=2)
        comp_img_pil = Image.fromarray(comp_img_rgba).convert("RGBA")
        
        gen, char, rating = await sharedRuntime.predict(comp_img_pil, threshold=0.35, character_threshold=0.35)
        pred_tags = list(gen.keys()) + list(char.keys())
        pred_tags = [t.lower() for t in pred_tags]
        
        if mode == "AND":
          match = all(any(t in pt for pt in pred_tags) for t in target_tags)
        else: # OR
          match = any(any(t in pt for pt in pred_tags) for t in target_tags)
            
        if match:
          final_mask = np.maximum(final_mask, comp_mask * 255)
      
      mask = final_mask.astype(np.float32)[:, :, np.newaxis] / 255.0
        
    output_img = np.concatenate((mask * img + 1 - mask, mask * 255), axis=2).astype(np.uint8)
    out_mask_img = (mask[:, :, 0] * 255).astype(np.uint8)
    
    if crop:
      x, y, w, h = cv2.boundingRect(out_mask_img)
      if w > 0 and h > 0:
        output_img = output_img[y:y+h, x:x+w]
        out_mask_img = out_mask_img[y:y+h, x:x+w]
        
    return out_mask_img, output_img