import gradio as gr
import os

from modules.character_template import CharacterTemplate
from modules.simple_template import SimpleTemplate
from webui import UiTabs

class Define(UiTabs):
    def __init__(self, path):
        super().__init__(path)

        self.child_path = os.path.join(UiTabs.PATH, "define_child")

    def title(self):
        return "Character-Template"

    def index(self):
        return 3

    def ui(self, outlet):
        module = CharacterTemplate()
        def validate_lora(lora):
            status = module.check_lora_trigger(lora)
            if status:
                gr.Info("LoRA Triggers correctly!")
            else:
                raise gr.Error("LoRA Triggers incorrectly!")

        with gr.Blocks():
            chara_version = gr.Dropdown(label="Template ver.", choices=["v3 Legacy", "v6"], value="v6")
            display_name = gr.Textbox(label="Display Name", placeholder="REQUIRED")

            with gr.Group(visible=False) as v3_group:
                with gr.Row():
                    lora_trig = gr.Textbox(label="LoRA Trigger (placeholder of $LORA)", placeholder="may <lora:name:w> style", scale=8)
                    check_lora = gr.Button("Validate", size="lg", elem_classes="center_button")
                    check_lora.click(
                        validate_lora, lora_trig
                    )
                with gr.Row():
                    name = gr.Textbox(label="placeholder of $NAME")
                    prompt = gr.Textbox(label="placeholder of $PROMPT")
                overwrite = gr.Checkbox(label="overwrite prv key")

                save = gr.Button("Save", variant="primary")
                save.click(
                    module.new_chara_v3,
                    inputs=[
                        chara_version, display_name, lora_trig, name, prompt, overwrite
                    ]
                )

            with gr.Group(visible=True) as v6_group:
                with gr.Row():
                    lora_trig6 = gr.Textbox(label="LoRA Trigger (placeholder of $LORA)", placeholder="may <lora:name:w> style", scale=6)
                    default_weight = gr.Slider(-2, 2, step=0.01, value=1, label="Default Weight", scale=4)
                    check_lora6 = gr.Button("Validate", size="lg", scale=1, elem_classes="center_button")
                    check_lora6.click(
                        validate_lora, lora_trig6
                    )

                with gr.Row():
                    name6 = gr.Textbox(label="placeholder of $NAME")
                    prompt6 = gr.Textbox(label="placeholder of $PROMPT")
                overwrite6 = gr.Checkbox(label="overwrite prv key")

                with gr.Accordion("Character types", elem_classes="accordion_style"):
                    with gr.Row():
                        keys = {}
                        value_key_label = "'s value (placeholder of $TYPE or add to footer)"
                        def append_key(k: str):
                            if k not in keys.keys():
                                keys[k] = ""
                                gr.Info(f"{k} created!")
                                return gr.update(
                                    choices=list(keys.keys()), value=k
                                )
                            else:
                                gr.Warning(f"{k} is already in the list.")
                                return gr.update(
                                    value=k
                                )

                        def delete_key(k: str):
                            if k in keys.keys():
                                keys.pop(k)
                                gr.Info(f"{k} deleted!")
                                return gr.update(
                                    choices=list(keys.keys()), value=""
                                ), gr.update(
                                    value=keys
                                )
                            else:
                                gr.Warning(f"{k} is not in the list.")
                                return gr.update(), gr.update()

                        def swap_key(k: str):
                            if k in keys.keys():
                                return gr.update(
                                    label=f"{k}{value_key_label}", value=keys[k]
                                )
                            else:
                                return None

                        def update_key(k: str, v: str):
                            if not k in keys.keys():
                                gr.Info(f"{k} created!")

                            keys[k] = v
                            return gr.update(
                                value=keys
                            )

                        current_key = gr.Dropdown(
                            scale=9, allow_custom_value=True,
                            choices=list(keys.keys()), value="", label="Key (type manually to add)"
                        )
                        with gr.Column():
                            add_key = gr.Button("Add", variant="secondary", scale=1, size="lg", elem_classes="luna724_green_button center_button") # TODO: current_key にない値が current_key に入っている場合に追加する
                            remove_key = gr.Button("Remove", variant="secondary", scale=1, size="lg", elem_classes="luna724_red_button center_button")

                    value_key = gr.Textbox(
                        label=f"key{value_key_label}"
                    )
                    submit_value = gr.Button(
                        "Submit pair", variant="primary", size="sm"
                    )

                    current_types = gr.JSON(
                        label="Current types", value={}
                    )

                    add_key.click(
                        # current_key に値を追加する
                        append_key, current_key, outputs=current_key
                    )
                    remove_key.click(
                        # remove_key から値を削除する
                        delete_key, current_key, outputs=[current_key, current_types]
                    )
                    current_key.change(
                        # current_key の内容を value_key に表示する
                        swap_key, current_key, outputs=value_key
                    )
                    submit_value.click(
                        # current_key, value_key の値を keys に保存する
                        # ついでに current_types に表示する
                        update_key,
                        [current_key, value_key],
                        outputs=current_types
                    )

                save6 = gr.Button("Save", variant="primary")
                save6.click(
                    module.new_chara_v6,
                    inputs=[
                        chara_version, display_name, lora_trig6, name6, prompt6,
                        default_weight, current_types, overwrite6
                    ]
                )

            def switch_version(version):
                if version == "v3 Legacy":
                    return gr.update(visible=True), gr.update(visible=False)
                elif version == "v6":
                    return gr.update(visible=False), gr.update(visible=True)

            chara_version.change(
                switch_version, chara_version, outputs=[v3_group, v6_group]
            )