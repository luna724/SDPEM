import gradio as gr
import os

import shared
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "caption_utils")

    def title(self):
        return "Pattern Resizer"

    def index(self):
        return 1

    def ui(self, outlet):
        gr.Markdown("## Pattern Resizer\nto use, write your code in the textbox.\nsrc are tag piece, return: resized tag or empty. empty to delete tag<br>\n[More Information]()")
        with gr.Blocks():
            replacing_code = gr.Textbox(
               label="Replacing Code (python)", lines=6,
               value="""def replace(src) -> str:
    return src.replace("censored", "")"""
            )
            with gr.Row():
                 tag = gr.Textbox(label="Tag", scale=5)
                 output = gr.Textbox(label="Output", scale=5)
                 eval_button = gr.Button("Test-Evaluate Code", variant="primary", scale=3)

            def evaluate_code(code, tag):
                try:
                    local_vars = {}
                    exec(code, {}, local_vars)
                    if 'replace' in local_vars:
                        result = local_vars['replace'](tag)
                        if result == "":
                            return f"Tag '{tag}' removed."
                        else:
                            return f"Tag '{tag}' replaced with '{result}'."
                    else:
                        return "No `replace` function found."
                except Exception as e:
                    raise gr.Error(f"Error occurred: {e}")

            eval_button.click(fn=evaluate_code, inputs=[replacing_code, tag], outputs=output)
            
            def run_main(
                code, target_dir, caption_ext, autoscale_caption, convert_to_space, convert_to_lowercase, png_exist_check
            ):
                if evaluate_code(code, "test") == "No `replace` function found.":
                    raise gr.Error("No `replace` function found. in your code")

                local_vars = {}
                exec(code, {}, local_vars)
                func = local_vars['replace']

                files = [
                    x for x in os.listdir(target_dir)
                    if os.path.splitext(x)[1].lower() == caption_ext.lower() and (
                       os.path.exists(os.path.splitext(x)[0] + '.png') or not png_exist_check)
                ]
                resized_caption = []

                for file in files:
                    path = os.path.join(target_dir, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        caption = f.read()

                    for c in caption.split(","):
                        if autoscale_caption:
                            c = c.strip()
                        if convert_to_space:
                            c = c.replace("_", " ")
                        if convert_to_lowercase:
                            c = c.lower()
                        c = func(c)
                        if not isinstance(c, str) and c is not None:
                            raise gr.Error(f"replace function must be return string but got {type(c)}")
                        if c == "" or c is None:
                            continue
                        resized_caption.append(c)

                    if autoscale_caption:
                        caption = ", ".join(resized_caption)
                    else:
                        caption = ",".join(resized_caption) + ","
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(caption)

            run = gr.Button("Run", variant="primary")

            default = shared.ui_obj["Caption-Util"]
            default_args = [default["target_dir"], default["caption_ext"], default["autoscale_caption"], default["convert_to_space"], default["convert_to_lowercase"], default["png_exist_check"]]
            run.click(fn=run_main, inputs=[replacing_code]+default_args)