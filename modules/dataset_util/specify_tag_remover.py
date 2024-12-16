import os

import gradio as gr

def run_ui(
        target_dir, caption_ext, autoscale_caption, convert_to_space, convert_to_lowercase,
        png_exist_check,
        remove_target_tags, separator, target_col, contained_tags, contain_detection_mode,
        cm_percentage, cm_count, warn_mode
):
    if separator == ";":
        raise gr.Error("Separator cannot contain ; (semicolon).")

    # 専用引数を事前処理
    remove_tags = []
    replace_tags = {} # k: src, v: dst

    target_columns = [
        int(i) for i in target_col.split(",")
        if i.isdigit()
    ]
    all_col = False
    if target_col.count("*") > 0:
        target_columns = ["*"]
        all_col = True

    # remove_target_tags を分解する
    for tag in remove_target_tags.split(separator):
        if "_" in tag and convert_to_space:
            tag = tag.replace("_", " ") # 互換性

        if ";" in tag: # replaceのチェック
            src = tag.split(";")[0]
            dst = ";".join(tag.split(";")[1:])
            replace_tags[src.strip().lower()] = dst.strip()
            continue

        remove_tags.append(tag.strip().lower())

    contain_tags = [x.strip().lower() for x in contained_tags.split(",")]

    files = [
        x for x in os.listdir(target_dir)
        if os.path.splitext(x)[1].lower() == caption_ext.lower() and (
            os.path.exists(os.path.splitext(x)[0] + '.png') or not png_exist_check
        )
    ]
    for file in files:
        path = os.path.abspath(os.path.join(target_dir, file))
        with open(path, "r", encoding="utf-8") as f:
            caption = f.read()
        caption_tags = [x.strip() for x in caption.split(",")]

        # contain check
        if len(contain_tags) != 0:
            ##TODO: contain check のモードを考慮した実装
            if not (set(contain_tags) & set(caption_tags)):
                continue # はいってないなら

