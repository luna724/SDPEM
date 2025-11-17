from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import json
from modules.utils.lora_util import list_lora, has_lora_tags, find_lora, read_lora_name, get_tag_freq_from_lora, LoRAMetadataReader
from modules.utils.ui.register import RegisterComponent, Path


class LoRAInfo(UiTabs):
    def title(self) -> str:
        return "LoRA Info"
    
    def index(self) -> int:
        return 4
    
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def get_lora_info(lora_name: str) -> tuple[str, str, str]:
            """Get LoRA information including name, tags, and metadata"""
            if not lora_name:
                return "No LoRA selected", "", ""
            
            try:
                lora_path = await find_lora(lora_name, allow_none=False)
                metadata_reader = LoRAMetadataReader(lora_path)
                
                if not metadata_reader.loadable:
                    return "Failed to load LoRA metadata", "", ""
                
                # Get LoRA trigger name
                trigger_name = metadata_reader.get_output_name(blank="N/A")
                
                # Get base model info
                base_model = metadata_reader.detect_base_model_for_ui()
                
                # Check if LoRA has tags
                has_tags = has_lora_tags(lora_name)
                
                # Build info text
                info_text = f"**LoRA Name:** {lora_name}\n"
                info_text += f"**Trigger Word:** {trigger_name}\n"
                info_text += f"**Base Model:** {base_model}\n"
                info_text += f"**Has Tags:** {'Yes' if has_tags else 'No'}\n"
                
                # Get tag frequencies if available
                tags_text = ""
                metadata_text = ""
                
                if has_tags:
                    try:
                        tag_freq, ss_tag_freq = await get_tag_freq_from_lora(lora_name)
                        
                        # Combine both tag frequencies
                        all_tags = {}
                        all_tags.update(tag_freq)
                        all_tags.update(ss_tag_freq)
                        
                        # Sort by frequency
                        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
                        
                        # Format top 100 tags
                        tags_text = ""
                        for tag, freq in sorted_tags:
                            tags_text += f"{tag}: {freq}\n"
                        
                        info_text += f"\n**Total Tags:** {len(all_tags)}\n"
                    except Exception as e:
                        tags_text = f"Error reading tags: {str(e)}"
                else:
                    tags_text = "No tag metadata available for this LoRA."
                
                # Get raw metadata
                try:
                    metadata_text = json.dumps(metadata_reader.metadata, indent=2, ensure_ascii=False)
                except Exception as e:
                    metadata_text = f"Error reading metadata: {str(e)}"
                
                return info_text, tags_text, all_tags, metadata_text
                
            except Exception as e:
                error_msg = f"Error loading LoRA info: {str(e)}"
                return error_msg, "", ""
        
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
            
            info_output = gr.Markdown(label="LoRA Information")
            with gr.Row():
                tags_output = gr.Textbox(
                    label="Tags",
                    lines=12,
                    max_lines=30,
                    interactive=False,
                )
                tags_label = gr.Label(
                    label="Tags", show_label=False
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
                outputs=[info_output, tags_output, tags_label, metadata_output],
            )
            
            def refresh_lora_list():
                return gr.update(choices=list_lora())
            
            refresh_btn.click(
                fn=refresh_lora_list,
                inputs=[],
                outputs=[lora_dropdown],
            )
