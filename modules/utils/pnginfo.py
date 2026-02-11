from PIL import Image, PngImagePlugin
import json
import gradio as gr

def make_info(
    info: dict[str, str]
) -> PngImagePlugin.PngInfo:
    i = PngImagePlugin.PngInfo() 
    for k, v in info.items():
        i.add_text(k, v)
    return i

async def read_pnginfo(
        img: Image.Image,
        clear_image: bool = False, only_prompt: bool = False, show_raw: bool = False
    ) -> tuple[str, Image.Image|None]:
    if img is None: raise gr.Error("No image provided")
    if not hasattr(img, "info"):
        raise gr.Error("Image has no metadata")
    
    info = img.info
    if show_raw: i = json.dumps(info, indent=2, ensure_ascii=False)
    else: i = info.get("parameters", "")
    if clear_image: img = None
    if only_prompt: i = i.split("\nNegative prompt: ")[0].strip()
    return i, img