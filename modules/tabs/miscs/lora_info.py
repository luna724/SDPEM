from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Any, Callable, Dict
from utils import *

from modules.utils.lora_util import list_lora, has_lora_tags, find_lora, read_lora_name, get_tag_freq_from_lora, LoRAMetadataReader, extract_external_lora_meta
from modules.utils.ui.register import RegisterComponent, Path


class LoRAInfo(UiTabs):
    def title(self) -> str:
        return "LoRA Info"
    
    def index(self) -> int:
        return 4
    
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def get_lora_info(
            lora_name: str,
        ) -> tuple[
            str,
            str,
            str,
            int,
            str,
            Dict[str, float],
            object | None,
            str,
            float,
            str,
            str,
            Dict[str, object],
        ]:
            """Get LoRA information including description details derived from metadata."""

            def default_response(message: str = "No tags available") -> tuple[
                str,
                str,
                str,
                int,
                str,
                Dict[str, float],
                object | None,
                str,
                float,
                str,
                str,
                Dict[str, object],
            ]:
                return (
                    "",
                    "",
                    "",
                    0,
                    message,
                    {},
                    None,
                    "",
                    1.0,
                    "",
                    "",
                    {},
                )

            if not lora_name:
                return default_response()

            try:
                lora_path = await find_lora(lora_name, allow_none=False)
                metadata_reader = LoRAMetadataReader(lora_path)

                if not metadata_reader.loadable:
                    message = "Failed to load LoRA metadata"
                    fallback = list(default_response(message))
                    fallback[0] = lora_name
                    fallback[1] = "N/A"
                    fallback[2] = "N/A"
                    fallback[-1] = {"error": message}
                    return tuple(fallback)  # type: ignore[return-value]

                external_metadata = await extract_external_lora_meta(lora_path)

                preview_image_value: object | None = None
                activation_text_value = ""
                preferred_weight_value = 1.0
                negative_text_value = ""
                notes_value = ""

                if isinstance(external_metadata, dict) and external_metadata:
                    preview_image_value = external_metadata.get("image")

                    activation_text_value = external_metadata.get("activation text") or ""

                    preferred_raw = external_metadata.get("preferred weight")
                    if preferred_raw is not None:
                        try:
                            preferred_weight_value = float(preferred_raw)
                        except (TypeError, ValueError):
                            preferred_weight_value = 1.0
                    preferred_weight_value = max(0.0, min(2.0, preferred_weight_value))

                    negative_text_value = external_metadata.get("negative text") or ""

                    notes_parts: list[str] = []
                    sd_version_text = external_metadata.get("sd version")
                    if sd_version_text:
                        notes_parts.append(f"SD Version: {sd_version_text}")
                    description_text = external_metadata.get("description")
                    if description_text:
                        notes_parts.append(description_text)
                    extra_notes = external_metadata.get("notes")
                    if extra_notes:
                        notes_parts.append(extra_notes)
                    notes_value = "\n".join(notes_parts)

                trigger_name = metadata_reader.get_output_name(blank="N/A")
                base_model = metadata_reader.detect_base_model_for_ui()

                if not activation_text_value and trigger_name != "N/A":
                    activation_text_value = trigger_name

                tags_text = ""
                tag_ratio: Dict[str, float] = {}
                total_tags = 0

                if has_lora_tags(lora_name):
                    try:
                        tag_freq, ss_tag_freq = await get_tag_freq_from_lora(lora_name)
                        all_tags: Dict[str, int] = {}
                        all_tags.update(tag_freq)
                        all_tags.update(ss_tag_freq)

                        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
                        total_tags = len(all_tags)

                        multi_weight_lines = [
                            f"{tag}: {freq}"
                            for tag, freq in sorted_tags
                            if freq > 1
                        ]
                        single_weight_tags = [
                            tag for tag, freq in sorted_tags if freq == 1
                        ]

                        sections: list[str] = []
                        if multi_weight_lines:
                            sections.append("\n".join(multi_weight_lines))
                        if single_weight_tags:
                            sections.append("-== weight 1 tags ==-\n" + ", ".join(single_weight_tags))

                        tags_text = "\n\n".join(sections) if sections else "No tags found"

                        total_frequency = sum(max(freq, 0) for _, freq in sorted_tags)
                        if total_frequency > 0:
                            for tag, freq in sorted_tags:
                                ratio = freq / total_frequency
                                if ratio >= 0.01:
                                    tag_ratio[tag] = round(ratio, 4)
                    except Exception as tag_error:
                        tags_text = f"Error reading tags: {tag_error}"
                else:
                    tags_text = "No tag metadata available for this LoRA."

                try:
                    metadata = metadata_reader.metadata or {}
                except Exception as metadata_error:
                    metadata = {"error": f"Error reading metadata: {metadata_error}"}
                    tag_ratio = {}

                return (
                    lora_name,
                    trigger_name,
                    base_model,
                    total_tags,
                    tags_text,
                    tag_ratio,
                    preview_image_value,
                    activation_text_value,
                    preferred_weight_value,
                    negative_text_value,
                    notes_value,
                    metadata,
                )

            except Exception as exc:
                message = f"Error loading LoRA info: {exc}"
                fallback = list(default_response(message))
                fallback[-1] = {"error": message}
                return tuple(fallback)  # type: ignore[return-value]
        
        lora_info_config = RegisterComponent(
            Path("./defaults/miscs.lora_info.json"),
            "miscs/lora_info",
        )
        r = lora_info_config.register
        default = lora_info_config.get()
        
        with gr.Blocks():
            with gr.Row():
                lora_dropdown = r(
                    "lora_name",
                    gr.Dropdown(
                        choices=list_lora(),
                        label="Select LoRA",
                        value=default.lora_name if hasattr(default, 'lora_name') else None,
                        scale=9,
                    ),
                )
                refresh_btn = gr.Button("🔄", variant="secondary", scale=1)
            
            with gr.Blocks():
                with gr.Row():
                    with gr.Column(scale=3):
                        lora_name_display = gr.Textbox(
                            label="LoRA Name",
                            value="",
                            interactive=False,
                        )
                        trigger_word_display = gr.Textbox(
                            label="LoRA Trigger",
                            value="",
                            interactive=False,
                        )
                    with gr.Column(scale=3):
                        base_model_display = gr.Textbox(
                            label="Base Model",
                            value="",
                            interactive=False,
                        )
                        tag_count_display = gr.Number(
                            label="Total Tags",
                            value=0,
                            interactive=False,
                        )
                    with gr.Column(scale=2):
                        ignore_rnd_lora = r(
                            "ignore_rnd_lora",
                            gr.Checkbox(
                                label="Ignore in rndLoRA (all)",
                                value=getattr(default, "ignore_rnd_lora", False),
                                info="Exclude this LoRA from rndLoRA (all) selection.",
                            ),
                        )

            with gr.Row():
                tags_output = gr.Textbox(
                    label="Tags",
                    lines=12,
                    max_lines=30,
                    interactive=False,
                )
                tag_ratio_label = gr.Label(
                    label="Tag Share",
                    value={},
                )
            
            with gr.Accordion(label="LoRA Desc", open=False):
                with gr.Row():
                    preview_image = gr.Image(
                        label="LoRA Preview Image", type="pil", interactive=False
                    )

                    with gr.Column():
                        activation_text = gr.Textbox(
                            label="Activation Text", lines=1, interactive=False, show_copy_button=True
                        )
                        preferred_weight = gr.Slider(
                            label="Preferred Weight", minimum=0.0, maximum=2.0, step=0.01, interactive=False
                        )
                        activation_neg = gr.Textbox(
                            label="Activation Negative prompt", lines=1, interactive=False, show_copy_button=True
                        )
                        notes = gr.Textbox(
                            label="Notes", lines=4, interactive=False, show_copy_button=True
                        )
            
            with gr.Accordion(label="Raw Metadata", open=True):
                metadata_output = gr.JSON(
                    label="Metadata",
                )
            
            # Event handlers
            lora_dropdown.change(
                fn=get_lora_info,
                inputs=[lora_dropdown],
                outputs=[
                    lora_name_display,
                    trigger_word_display,
                    base_model_display,
                    tag_count_display,
                    tags_output,
                    tag_ratio_label,
                    preview_image,
                    activation_text,
                    preferred_weight,
                    activation_neg,
                    notes,
                    metadata_output,
                ],
            )
            
            def refresh_lora_list():
                return gr.update(choices=list_lora())
            
            refresh_btn.click(
                fn=refresh_lora_list,
                inputs=[],
                outputs=[lora_dropdown],
            )
            
            
