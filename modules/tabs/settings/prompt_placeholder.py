from webui import UiTabs
import gradio as gr
from typing import Callable
from utils import *
from pathlib import Path
from modules.utils.ui.register import RegisterComponent
from modules.utils.ui.elements import return_empty
from modules.prompt_placeholder import placeholder

class Prompt(UiTabs):
    def title(self) -> str:
        return "Placeholder"
    def index(self) -> int:
        return 1

    async def ui(self, outlet: Callable[[str, gr.components.Component], None]):
        placeholder_setting = RegisterComponent(
            Path("./defaults/prompt_placeholder.json"),
            "settings/prompt_placeholder",
        )
        r = placeholder_setting.register
        default = placeholder_setting.get()
        VERSION = 1.0
        DATA_VERSION = 1.0
        
        async def run(
            before, after, desc: str,
            key: str, target: list[str], 
            pattern: str, escape: bool, flags: list[str],
            replace: bool, atLeast: int, is_new: bool, ver: str
        ):
            if float(ver) != VERSION: raise gr.Error("Version mismatch, please reload the page")
            data = {
                "name": after,
                "description": desc,
                "version": VERSION,
                "data": {
                    "version": DATA_VERSION,
                    "key": key,
                    "matchTo": target,
                    "if": {
                        "patternTemplate": pattern,
                        "escape": escape,
                        "flags": flags,
                        "replace": replace,
                        "atLeast": atLeast,
                    },
                }
            }
            if is_new:
                res = placeholder.push(after, data)
                if res:
                    gr.Info(f"Added new placeholder '{after}'")
                else:
                    raise gr.Error(f"Placeholder with name '{after}' already exists. (please choose in \"Edit target\" dropdown)")
            else: # Edit / update
                if before != after:
                    rem_res = placeholder.delete(before)
                    gr.Info(f"Removed placeholder '{before}'")
                placeholder.update(after, data)
                gr.Info(f"Added new placeholder '{after}'")
            return gr.update(choices=placeholder.all_names(), value=after), False
        
        
        with gr.Row():
            target = r(
                "target",
                gr.Dropdown(
                    label="Edit target", scale=8,
                    choices=placeholder.all_names(),
                    value=None
                ), order=0
            )
            create_new = gr.Button(
                "Create New", scale=2, variant="primary"
            )
            
            
        with gr.Row():
            delete = gr.Button("Delete", variant="stop")
            
        
        with gr.Blocks():
            with gr.Row():
                name = r(
                    "name",
                    gr.Textbox(
                        label="Name",
                        placeholder="Enter a unique name for this placeholder setting",
                        scale=8,
                        max_lines=1,
                    ), order=1
                )
                version = gr.Textbox(
                    interactive=False, scale=2, label="Version",
                    value=str(VERSION)
                )
                
            description = r(
                "description",
                gr.Textbox(
                    label="Description",
                    placeholder="Describe the purpose of this placeholder setting",
                    lines=1, max_lines=400,
                    scale=7,
                ), order=2
            )
            with gr.Column():
                placeholder_key = r(
                    "placeholder_key",
                    gr.Textbox(
                        label="Placeholder Key",
                        placeholder="replace to this key",
                        lines=1,
                    ), order=3
                )
                with gr.Group():
                    match_target = r(
                        "match_target",
                        gr.Dropdown(
                            label="Match Target",
                            interactive=True, choices=[], multiselect=True,
                        ), order=4
                    )
                    match_to_field = gr.Textbox(
                        label="Match Target (input field)",
                        placeholder="Enter tags to match, shift+enter to add",
                        lines=4, interawctive=True, 
                    )
                    
                    def update_match_to(curr, field: str):
                        if field.strip() == "": return gr.update(), ""
                        curr.append(field)
                        
                        return gr.update(
                            value=curr, choices=curr
                        ), ""
                        
                    match_to_field.submit(
                        fn=update_match_to,
                        inputs=[match_target, match_to_field],
                        outputs=[match_target, match_to_field],
                        show_progress=True,
                    )
                    
                
            with gr.Accordion("Optional settings", open=False):
                version_ = gr.Textbox(label="Data Version", value=str(DATA_VERSION), interactive=False)
                
                with gr.Row():
                    pattern = r(
                        "pattern",
                        gr.Textbox(
                        label="Pattern Template",
                        value=r"^\s*{MATCH}\s*$",
                        info="regex ({MATCH} will be replaced with match_target)", scale=9
                        ), order=5
                    )   
                    escape = r(
                        "escape", 
                        gr.Checkbox(label="Escape Match Target", info="re.escape(match_target)", value=False, scale=1
                        ), order=6
                    )
                with gr.Row():
                    flags = r(
                        "flags",
                        gr.Dropdown(
                            label="Regex Flags", choices=[
                                "ASCII", "IGNORECASE", "LOCALE", "MULTILINE", "DOTALL", "VERBOSE", "UNICODE"
                            ], multiselect=True, value=["IGNORECASE"], scale=8
                        ), order=7
                    )
                    replace = r(
                        "replace",
                        gr.Checkbox(label="Replace Matched Prompt", value=True, scale=2,
                        info="if unchecked, means do nothing"
                        ), order=8
                    )
                
                atLeast = r(
                    "atLeast",
                    gr.Number(label="At Least", value=1, precision=0), order=9
                )
            is_new = gr.Checkbox(value=True,visible=False)
            
            variables = placeholder_setting.ordered_values() + [
                is_new, version
            ]
            
            run_btn = gr.Button("Save Placeholder", variant="primary")
            run_btn.click(
                fn=run, inputs=variables, 
                outputs=[
                    target, is_new,
                ]
            )
            
            def on_target_change_a(
                name: str
            ):
                return not name in placeholder.all_names()
            def on_target_change_b(
                name: str
            ):
                if not name in placeholder.all_names(): 
                    return return_empty(9)
                data = placeholder.get(name)
                d = data.get("data", {})
                i = d.get("if", {})
                return (
                    data.get("name", ""), 
                    data.get("description", ""),
                    d.get("key", ""), 
                    gr.Dropdown.update(value=d.get("matchTo", []), choices=d.get("matchTo", [])),
                    i.get("patternTemplate", r"\b{MATCH}\b"), i.get("escape", True), i.get("flags", ["IGNORECASE"]), i.get("replace", True), i.get("atLeast", 1),
                )
                
            target.input( 
                fn=on_target_change_a,
                inputs=target,
                outputs=is_new
            )
            target.input(
                fn=on_target_change_b,
                inputs=target,
                outputs=[
                    name, description, placeholder_key, match_target, pattern, escape, flags, replace, atLeast
                ]
            )
            
            def on_create_new():
                return None, True
            create_new.click(
                fn=on_create_new,
                outputs=[target, is_new],
            )
            
            def delete_button(n):
                if n is None or n not in placeholder.all_names():
                    raise gr.Error("Please select a valid target to delete")
                placeholder.delete(n)
                return gr.update(choices=placeholder.all_names(), value=None), True
            delete.click(
                fn=delete_button,
                inputs=target,
                outputs=[target, is_new],
            )