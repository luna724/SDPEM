from modules.tag_compare import TagCompareUtilities
from webui import UiTabs
import modules.bert
import modules.tag_compare

import os
import gradio as gr


class Template(UiTabs):
    def __init__(self, path):
        super().__init__(path)
        self.child_path = os.path.join(UiTabs.PATH, "test_child")

    def title(self):
        return "Text-emb compare"

    def index(self):
        return 0

    def ui(self, outlet):
        tag_compare_util = TagCompareUtilities()
        max_fields = 10  # 最大フィールド数
        textboxes = [gr.Textbox(label=f"Prompt {i + 1}", visible=False) for i in range(max_fields)]

        def update_visibility(num_fields):
            num_fields = int(num_fields)
            updates = []
            for i in range(max_fields):
                if i < num_fields:
                    updates.append(gr.update(visible=True))
                else:
                    updates.append(gr.update(visible=False, value=""))
            return updates

        def compare(*args):
            num_fields = args[max_fields:][0]
            threshold = args[max_fields:][1]
            compare_mode = args[max_fields:][2].lower()
            visible_inputs = args[:num_fields]

            if compare_mode == "bert":
                return modules.bert.default.compare_multiply_words(visible_inputs, threshold) # ignore: type
            else:
                return tag_compare_util.compare_multiply_words_for_ui(visible_inputs, threshold) # ignore: type

        with gr.Blocks():
            num_fields_input = gr.Slider(label="Number of prompts to compare", value=0, minimum=2, maximum=10, step=1)
            with gr.Row():
                compare_mode = gr.Radio(
                    choices=["BERT", "FastText & Word2Vec"],
                    value="FastText & Word2Vec", label="Compare mode (to tag, fasttext recommended, to literal string, BERT recommended)",
                    scale=7
                )
                threshold = gr.Slider(0, 1, step=0.05, value=0.75, label="Threshold", scale=3)
            submit_button = gr.Button("submit")
            output = gr.Textbox(label="compare output")

            num_fields_input.input(update_visibility, inputs=num_fields_input, outputs=textboxes)
            submit_button.click(
                compare,
                inputs=textboxes+[
                    num_fields_input, threshold, compare_mode
                ],
                outputs=output
            )