from PIL import Image, PngImagePlugin

def make_info(
    info: dict[str, str]
) -> PngImagePlugin.PngInfo:
    i = PngImagePlugin.PngInfo() 
    for k, v in info.items():
        i.add_text(k, v)
    return i