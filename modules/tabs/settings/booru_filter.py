from webui import UiTabs
import gradio as gr
import shared
from typing import Callable
from utils import *
from pathlib import Path

from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent
from modules.booru_filter import booru_filter

class Prompt(UiTabs):
    def title(self) -> str:
        return "Booru Filter"
    def index(self) -> int:
        return 2

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]):
        booru_filter_rc = RegisterComponent(
            Path("./defaults/booru_filter.json"),
            "settings/booru_filter",
        )
        r = booru_filter_rc.register
        default = booru_filter_rc.get()

        with gr.Row():
            filter_enable = r(
                "filter_enable",
                gr.Checkbox(
                    value=default.filter_enable,
                    label="Enable Caption Filter",
                ),
            )
            model = r(
                "model",
                gr.Dropdown(
                    choices=[
                        x["display_name"]
                        for x in shared.models["wd-tagger"]
                    ],  # TODO: wd以外のtaggerからも取得するように
                    value=default.model,
                    label="Tagger Model",
                ),
            )
        with gr.Row():
            threshold = r(
                "threshold",
                gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=default.threshold or 0.65,
                    label="Caption Filter Threshold",
                    step=0.01,
                    info="Threshold for the caption filter",
                ),
            )
            character_threshold = r(
                "character_threshold",
                gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=default.character_threshold or 0.45,
                    label="Character Filter Threshold",
                    step=0.01,
                    info="Threshold for the character filter",
                ),
            )
        with gr.Row():
            allow_rating = r(
                "allow_rating",
                gr.Dropdown(
                    choices=[
                        "general",
                        "sensitive",
                        "questionable",
                        "explicit",
                    ],
                    value=default.allow_rating
                    or ["general", "sensitive", "questionable", "explicit"],
                    multiselect=True,
                    label="[wip] Allow Ratings",
                    scale=6,
                ),
            )
            ignore_questionable = r(
                "ignore_questionable",
                gr.Checkbox(
                    value=default.ignore_questionable,
                    label="Ignore Questionable",
                    info="If enabled, questionable weight will be ignored (questionable 99%, sensitive 1% will be treated as sensitive 100%)",
                    scale=4,
                ),
            )

        with gr.Accordion(label="Save Option", open=False):

            def set_visible_from_rating(allow_rate):
                g = "general" in allow_rate
                s = "sensitive" in allow_rate
                q = "questionable" in allow_rate
                e = "explicit" in allow_rate
                return (
                    gr.update(visible=g),
                    gr.update(visible=s),
                    gr.update(visible=q),
                    gr.update(visible=e),
                )

            with gr.Row():
                save_each_rate = r(
                    "save_each_rate",
                    gr.Checkbox(
                        value=default.save_each_rate,
                        label="Save Each Rating",
                    ),
                )

                merge_sensitive = r(
                    "merge_sensitive",
                    gr.Checkbox(
                        value=default.merge_sensitive,
                        label="Merge Sensitive to general",
                    ),
                )
            with gr.Row(visible=True) as general_row:
                general_save_dir = r(
                    "general_save_dir",
                    gr.Textbox(
                        label="[Rating] General Save Directory",
                        placeholder="Enter the general save directory",
                        value=default.general_save_dir
                        or os.path.join(
                            shared.api_path,
                            "outputs/txt2img-images/{DATE}-pem/general",
                        ),
                        lines=1,
                        max_lines=1,
                        scale=19,
                    ),
                )
                general_browse_dir = gr.Button(
                    "📁", variant="secondary", scale=1
                )
                general_browse_dir.click(
                    fn=select_folder, outputs=[general_save_dir]
                )
            with gr.Row(visible=True) as sensitive_row:
                sensitive_save_dir = r(
                    "sensitive_save_dir",
                    gr.Textbox(
                        label="[Rating] Sensitive Save Directory",
                        placeholder="Enter the sensitive save directory",
                        value=default.sensitive_save_dir
                        or os.path.join(
                            shared.api_path,
                            "outputs/txt2img-images/{DATE}-pem/sensitive",
                        ),
                        lines=1,
                        max_lines=1,
                        scale=19,
                    ),
                )
                sensitive_browse_dir = gr.Button(
                    "📁", variant="secondary", scale=1
                )
                sensitive_browse_dir.click(
                    fn=select_folder, outputs=[sensitive_save_dir]
                )

            with gr.Row(visible=True) as questionable_row:
                questionable_save_dir = r(
                    "questionable_save_dir",
                    gr.Textbox(
                        label="[Rating] Questionable Save Directory",
                        placeholder="Enter the questionable save directory",
                        value=default.questionable_save_dir
                        or os.path.join(
                            shared.api_path,
                            "outputs/txt2img-images/{DATE}-pem/questionable",
                        ),
                        lines=1,
                        max_lines=1,
                        scale=19,
                    ),
                )
                questionable_browse_dir = gr.Button(
                    "📁", variant="secondary", scale=1
                )
                questionable_browse_dir.click(
                    fn=select_folder, outputs=[questionable_save_dir]
                )

            with gr.Row(visible=True) as explicit_row:
                explicit_save_dir = r(
                    "explicit_save_dir",
                    gr.Textbox(
                        label="[Rating] Explicit Save Directory",
                        placeholder="Enter the explicit save directory",
                        value=default.explicit_save_dir
                        or os.path.join(
                            shared.api_path,
                            "outputs/txt2img-images/{DATE}-pem/explicit",
                        ),
                        lines=1,
                        max_lines=1,
                        scale=19,
                    ),
                )
                explicit_browse_dir = gr.Button(
                    "📁", variant="secondary", scale=1
                )
                explicit_browse_dir.click(
                    fn=select_folder, outputs=[explicit_save_dir]
                )

            allow_rating.change(
                fn=set_visible_from_rating,
                inputs=[allow_rating],
                outputs=[
                    general_row,
                    sensitive_row,
                    questionable_row,
                    explicit_row,
                ],
            )
        with gr.Row():
            blacklist = r(
                "blacklist",
                gr.Textbox(
                    label="Caption Blacklist",
                    placeholder="Enter caption tags to blacklist, separated by commas",
                    info="if this tag is in the caption, the image will be skipped (or saved at other directory if enabled)",
                    lines=5,
                    max_lines=400,
                    value=default.blacklist or "",
                    scale=6,
                ),
            )
            pattern_blacklist = r(
                "pattern_blacklist",
                gr.Textbox(
                    label="Caption Blacklist Patterns",
                    placeholder="Enter caption patterns to blacklist, separated by lines",
                    info="if this pattern matches the caption, the image will be skipped (or saved at other directory if enabled)",
                    lines=5,
                    max_lines=10000,
                    value=default.pattern_blacklist or "",
                    scale=6,
                ),
            )
        with gr.Row():
            save_blacklisted = r(
                "save_blacklisted",
                gr.Checkbox(
                    value=default.save_blacklisted,
                    label="Blacklisted Save Option",
                    info="If enabled, blacklisted images will be saved to separate directory",
                    scale=10,
                ),
            )
            blacklist_save_dir = r(
                "blacklist_save_dir",
                gr.Textbox(
                    label="Blacklisted Save Directory",
                    placeholder="Enter the blacklisted save directory",
                    value=default.blacklist_save_dir
                    or os.path.join(
                        shared.api_path,
                        "C:/Users/luna_/Pictures/blacklisted",
                    ),
                    scale=19,
                ),
            )
            blacklist_browse_dir = gr.Button(
                "📁", variant="secondary", scale=1
            )
            blacklist_browse_dir.click(
                fn=select_folder, outputs=[blacklist_save_dir]
            )
        
        async def push(*args):
            booru_filter_rc.save(args)
            gr.Info("Saved")
            return await booru_filter.push_ui(*args)
            
        apply = gr.Button("Apply", variant="primary", )
        apply.click(
            fn=push,
            inputs=booru_filter_rc.values(),
        )