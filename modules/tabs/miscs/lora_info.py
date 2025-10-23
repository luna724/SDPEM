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
                        tags_text = "**Tag Frequencies (Top 100):**\n\n"
                        for tag, freq in sorted_tags[:100]:
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
                
                return info_text, tags_text, metadata_text
                
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
            gr.Markdown("# LoRA Information Viewer")
            gr.Markdown("View detailed information about LoRA models including trigger words, tags, and metadata.")
            
            with gr.Row():
                lora_dropdown = r(
                    "lora_name",
                    gr.Dropdown(
                        choices=list_lora(),
                        label="Select LoRA",
                        value=default.lora_name if hasattr(default, 'lora_name') else None,
                        scale=8,
                    ),
                )
                refresh_btn = gr.Button("🔄 Refresh List", variant="secondary", scale=1)
            
            with gr.Row():
                load_btn = gr.Button("Load LoRA Info", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    info_output = gr.Markdown(label="LoRA Information")
                    
            with gr.Accordion(label="Tag Frequencies", open=True):
                tags_output = gr.Textbox(
                    label="Tags",
                    lines=15,
                    max_lines=30,
                    interactive=False,
                )
            
            with gr.Accordion(label="Raw Metadata", open=False):
                metadata_output = gr.Textbox(
                    label="Metadata",
                    lines=15,
                    max_lines=30,
                    interactive=False,
                )
            
            # Event handlers
            load_btn.click(
                fn=get_lora_info,
                inputs=[lora_dropdown],
                outputs=[info_output, tags_output, metadata_output],
            )
            
            def refresh_lora_list():
                return gr.update(choices=list_lora())
            
            refresh_btn.click(
                fn=refresh_lora_list,
                inputs=[],
                outputs=[lora_dropdown],
            )
            
            # Save config
            save_btn = gr.Button("Save Configuration", variant="secondary")
            save_btn.click(
                fn=lora_info_config.insta_save,
                inputs=lora_info_config.values(),
                outputs=[],
            )
