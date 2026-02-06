"""
Database Logger for SDPEM
Generation log and tag statistics management system.
"""

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from modules.config import get_config
config = get_config()

# Get project root directory (parent of modules directory)
_current_file = Path(__file__).resolve()
_database_module_parent = _current_file.parent.parent
PROJECT_ROOT = _database_module_parent.parent


class TagStatsManager:
    """Manager for tag statistics, saves to individual JSON files."""
    
    # Threshold for determining if a tag was detected
    DETECTION_THRESHOLD = 0.5
    
    def __init__(self, stats_dir: str):
        self.stats_dir = stats_dir
    
    def _sanitize_tag_name(self, tag_name: str) -> str:
        """
        Sanitize tag name for use as filename.
        Replace special characters with '？'.
        
        Args:
            tag_name: Original tag name
        
        Returns:
            Sanitized tag name safe for filesystem
        """
        # Replace characters that are invalid in filenames
        # Windows: < > : " / \ | ? *
        # Also replace other special characters with ？
        invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
        return re.sub(invalid_chars, '？', tag_name)
    
    def _get_tag_path(self, tag_name: str) -> Path:
        """Get file path for a tag's statistics."""
        sanitized_name = self._sanitize_tag_name(tag_name)
        return Path(self.stats_dir) / f"{sanitized_name}.json"
    
    def load_tag_stats(self, tag_name: str) -> Optional[TagStats]:
        """
        Load statistics for a specific tag.
        
        Args:
            tag_name: Name of the tag
        
        Returns:
            TagStats object or None if not found
        """
        path = self._get_tag_path(tag_name)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return TagStats.model_validate(data)
        except Exception as e:
            print(f"Error loading tag stats for '{tag_name}': {e}")
            return None
    
    def save_tag_stats(self, stats: TagStats) -> bool:
        """
        Save statistics for a specific tag.
        
        Args:
            stats: TagStats object to save
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = self._get_tag_path(stats.tag_name)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(stats.model_dump_json(ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print(f"Error saving tag stats for '{stats.tag_name}': {e}")
            return False
    
    def update_from_log(self, log: GenerationLog):
        """
        Update tag statistics based on a generation log.
        
        Args:
            log: GenerationLog to process
        """
        # Track which tags were detected above threshold
        detected_tags = {
            tag.tag for tag in log.inferred_tags 
            if tag.score > self.DETECTION_THRESHOLD
        }
        
        # Update stats for each prompt tag
        for tag in log.prompt_tags:
            stats = self.load_tag_stats(tag) or TagStats(tag_name=tag)
            
            # Increment usage count
            stats.usage_count += 1
            
            # Increment detection count if tag was detected
            if tag in detected_tags:
                stats.detection_count += 1
            
            # Increment keep count if user kept this generation
            if log.user_action == "keep":
                stats.keep_count += 1
            
            # Recalculate rates
            if stats.usage_count > 0:
                stats.detection_rate = (stats.detection_count / stats.usage_count) * 100
                stats.keep_rate = (stats.keep_count / stats.usage_count) * 100
            
            # Update co-occurrence data
            self._update_cooccurrence(stats, log.prompt_tags)
            
            # Save updated stats
            self.save_tag_stats(stats)
    
    def _update_cooccurrence(self, stats: TagStats, all_tags: List[str]):
        """
        Update co-occurrence data for a tag.
        
        Args:
            stats: TagStats to update
            all_tags: All tags from the current generation
        """
        # Create a dict of current co-occurrences for easy lookup
        cooccur_dict = {item.tag: item for item in stats.cooccurrence}
        
        # Update co-occurrence counts
        for tag in all_tags:
            if tag != stats.tag_name:
                if tag in cooccur_dict:
                    cooccur_dict[tag].frequency += 1
                else:
                    cooccur_dict[tag] = TagCooccurrence(tag=tag, frequency=1)
        
        # Convert back to list and sort by frequency (keep top 20)
        stats.cooccurrence = sorted(
            cooccur_dict.values(),
            key=lambda x: x.frequency,
            reverse=True
        )[:20]
    
    def batch_update_from_logs(self, logs: List[GenerationLog]):
        """
        Batch update tag statistics from multiple logs.
        
        Args:
            logs: List of GenerationLog objects to process
        """
        for log in logs:
            self.update_from_log(log)
    
    def get_all_tag_names(self) -> List[str]:
        """
        Get all tag names that have statistics files.
        
        Returns:
            List of tag names
        """
        stats_path = Path(self.stats_dir)
        if not stats_path.exists():
            return []
        
        tag_names = []
        for file_path in stats_path.glob("*.json"):
            # Load the file to get the actual tag name (not sanitized filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'tag_name' in data:
                        tag_names.append(data['tag_name'])
            except Exception:
                continue
        
        return tag_names
