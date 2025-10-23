from webui import UiTabs
import gradio as gr
import os
import shared
from typing import Callable
from utils import *

import json
from PIL import Image
from modules.tagger.predictor import OnnxRuntimeTagger
from modules.utils.browse import select_folder
from modules.utils.ui.register import RegisterComponent, Path
from collections import Counter


class AutoBlacklistManager(UiTabs):
    def title(self) -> str:
        return "Auto-Blacklist Manager"
    
    def index(self) -> int:
        return 5
    
    def ui(self, outlet: Callable[[str, gr.components.Component], None]) -> None:
        async def analyze_images(
            acceptable_dirs: str,
            undesirable_dir: str,
            tagger_model: str,
            threshold: float,
            character_threshold: float,
        ) -> tuple[str, str, str]:
            """Analyze acceptable and undesirable images to suggest blacklist entries"""
            
            if not acceptable_dirs or not undesirable_dir:
                return "Please specify both acceptable and undesirable image directories.", "", ""
            
            # Initialize tagger
            try:
                tagger = OnnxRuntimeTagger(model_path=tagger_model, find_path=True)
                await tagger.load_model_cuda()
            except Exception as e:
                return f"Error loading tagger model: {str(e)}", "", ""
            
            acceptable_tags = Counter()
            undesirable_tags = Counter()
            
            # Process acceptable images
            acceptable_count = 0
            for acceptable_dir in acceptable_dirs.split(","):
                acceptable_dir = acceptable_dir.strip()
                if not os.path.exists(acceptable_dir):
                    continue
                    
                for img_file in os.listdir(acceptable_dir):
                    if not img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        continue
                    
                    try:
                        img_path = os.path.join(acceptable_dir, img_file)
                        img = Image.open(img_path).convert("RGBA")
                        
                        tags, character_tags, rating = await tagger.predict(
                            img,
                            threshold=threshold,
                            character_threshold=character_threshold,
                        )
                        
                        # Count tags
                        for tag in tags.keys():
                            acceptable_tags[tag] += 1
                        for tag in character_tags.keys():
                            acceptable_tags[tag] += 1
                        
                        acceptable_count += 1
                    except Exception as e:
                        warn(f"Error processing {img_file}: {e}")
            
            # Process undesirable images
            undesirable_count = 0
            if os.path.exists(undesirable_dir):
                for img_file in os.listdir(undesirable_dir):
                    if not img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        continue
                    
                    try:
                        img_path = os.path.join(undesirable_dir, img_file)
                        img = Image.open(img_path).convert("RGBA")
                        
                        tags, character_tags, rating = await tagger.predict(
                            img,
                            threshold=threshold,
                            character_threshold=character_threshold,
                        )
                        
                        # Count tags
                        for tag in tags.keys():
                            undesirable_tags[tag] += 1
                        for tag in character_tags.keys():
                            undesirable_tags[tag] += 1
                        
                        undesirable_count += 1
                    except Exception as e:
                        warn(f"Error processing {img_file}: {e}")
            
            # Unload tagger
            await tagger.unload_model()
            
            if acceptable_count == 0 or undesirable_count == 0:
                return "Not enough images to analyze. Please ensure both directories have images.", "", ""
            
            # Calculate tag frequencies
            acceptable_freq = {tag: count / acceptable_count for tag, count in acceptable_tags.items()}
            undesirable_freq = {tag: count / undesirable_count for tag, count in undesirable_tags.items()}
            
            # Find tags that appear frequently in undesirable but rarely in acceptable
            blacklist_candidates = []
            for tag, undes_freq in undesirable_freq.items():
                acc_freq = acceptable_freq.get(tag, 0)
                
                # Tag appears in >50% of undesirable images but <20% of acceptable images
                if undes_freq > 0.5 and acc_freq < 0.2:
                    difference = undes_freq - acc_freq
                    blacklist_candidates.append((tag, difference, undes_freq, acc_freq))
            
            # Sort by difference
            blacklist_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Find tags that appear frequently in acceptable but rarely in undesirable
            allowlist_candidates = []
            for tag, acc_freq in acceptable_freq.items():
                undes_freq = undesirable_freq.get(tag, 0)
                
                # Tag appears in >50% of acceptable images but <20% of undesirable images
                if acc_freq > 0.5 and undes_freq < 0.2:
                    difference = acc_freq - undes_freq
                    allowlist_candidates.append((tag, difference, acc_freq, undes_freq))
            
            # Sort by difference
            allowlist_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Format results
            summary = f"**Analysis Summary**\n\n"
            summary += f"Acceptable images analyzed: {acceptable_count}\n"
            summary += f"Undesirable images analyzed: {undesirable_count}\n"
            summary += f"Blacklist candidates found: {len(blacklist_candidates)}\n"
            summary += f"Allowlist suggestions found: {len(allowlist_candidates)}\n"
            
            blacklist_text = "**Suggested Blacklist Tags:**\n\n"
            blacklist_text += "Format: tag (appears in X% undesirable, Y% acceptable)\n\n"
            for tag, diff, undes_freq, acc_freq in blacklist_candidates[:50]:
                blacklist_text += f"{tag} ({undes_freq*100:.1f}% undesirable, {acc_freq*100:.1f}% acceptable)\n"
            
            # Generate comma-separated list for easy copying
            blacklist_csv = ", ".join([tag for tag, _, _, _ in blacklist_candidates[:50]])
            
            allowlist_text = "**Suggested Allowlist Tags:**\n\n"
            allowlist_text += "Format: tag (appears in X% acceptable, Y% undesirable)\n\n"
            for tag, diff, acc_freq, undes_freq in allowlist_candidates[:50]:
                allowlist_text += f"{tag} ({acc_freq*100:.1f}% acceptable, {undes_freq*100:.1f}% undesirable)\n"
            
            return summary, blacklist_text, blacklist_csv
        
        blacklist_config = RegisterComponent(
            Path("./defaults/miscs.auto_blacklist.json"),
            "miscs/auto_blacklist",
        )
        r = blacklist_config.register
        default = blacklist_config.get()
        
        with gr.Blocks():
            gr.Markdown("# Auto-Blacklist Manager")
            gr.Markdown("""
            This tool analyzes acceptable and undesirable images to automatically suggest tags for your blacklist.
            
            **How to use:**
            1. Specify directories containing acceptable images (multiple directories separated by commas)
            2. Specify the directory containing undesirable images
            3. Click 'Analyze Images' to get suggestions
            4. Copy suggested tags to your blacklist configuration
            """)
            
            with gr.Row():
                acceptable_dirs = r(
                    "acceptable_dirs",
                    gr.Textbox(
                        label="Acceptable Image Directories (comma-separated)",
                        placeholder="e.g., /path/to/good/general, /path/to/good/sensitive",
                        value=default.acceptable_dirs if hasattr(default, 'acceptable_dirs') else "",
                        lines=2,
                        scale=19,
                    ),
                )
                acceptable_browse = gr.Button("📁", variant="secondary", scale=1)
            
            with gr.Row():
                undesirable_dir = r(
                    "undesirable_dir",
                    gr.Textbox(
                        label="Undesirable Image Directory",
                        placeholder="/path/to/blacklisted/images",
                        value=default.undesirable_dir if hasattr(default, 'undesirable_dir') else "",
                        lines=1,
                        scale=19,
                    ),
                )
                undesirable_browse = gr.Button("📁", variant="secondary", scale=1)
            
            with gr.Row():
                tagger_model = r(
                    "tagger_model",
                    gr.Dropdown(
                        choices=[x["display_name"] for x in shared.models["wd-tagger"]],
                        label="Tagger Model",
                        value=default.tagger_model if hasattr(default, 'tagger_model') else "WD1.4 Vit Tagger v3 (large)",
                    ),
                )
                threshold = r(
                    "threshold",
                    gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=default.threshold if hasattr(default, 'threshold') else 0.65,
                        label="Tag Threshold",
                        step=0.01,
                    ),
                )
                character_threshold = r(
                    "character_threshold",
                    gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=default.character_threshold if hasattr(default, 'character_threshold') else 0.45,
                        label="Character Threshold",
                        step=0.01,
                    ),
                )
            
            analyze_btn = gr.Button("Analyze Images", variant="primary", size="lg")
            
            with gr.Row():
                summary_output = gr.Markdown(label="Analysis Summary")
            
            with gr.Accordion(label="Suggested Blacklist Tags", open=True):
                blacklist_output = gr.Textbox(
                    label="Blacklist Suggestions",
                    lines=15,
                    max_lines=30,
                    interactive=False,
                )
            
            with gr.Accordion(label="Blacklist (Comma-separated for easy copying)", open=True):
                blacklist_csv = gr.Textbox(
                    label="Copy this to your blacklist",
                    lines=5,
                    max_lines=10,
                    interactive=True,
                )
            
            # Event handlers
            acceptable_browse.click(
                fn=select_folder,
                inputs=[],
                outputs=[acceptable_dirs],
            )
            
            undesirable_browse.click(
                fn=select_folder,
                inputs=[],
                outputs=[undesirable_dir],
            )
            
            analyze_btn.click(
                fn=analyze_images,
                inputs=[
                    acceptable_dirs,
                    undesirable_dir,
                    tagger_model,
                    threshold,
                    character_threshold,
                ],
                outputs=[summary_output, blacklist_output, blacklist_csv],
            )
            
            # Save config
            save_btn = gr.Button("Save Configuration", variant="secondary")
            save_btn.click(
                fn=blacklist_config.insta_save,
                inputs=blacklist_config.values(),
                outputs=[],
            )
