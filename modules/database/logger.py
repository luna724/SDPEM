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
from pydantic import BaseModel, Field


# Get project root directory (parent of modules directory)
_current_file = Path(__file__).resolve()
_modules_dir = _current_file.parent.parent
PROJECT_ROOT = _modules_dir.parent


# ================================================================================
# A. Generation Log Models
# ================================================================================

class MismatchData(BaseModel):
    """Mismatch data between input and output tags."""
    lost: List[str] = Field(default_factory=list, description="Tags present in input but not detected in output")
    ghost: List[str] = Field(default_factory=list, description="Tags not in input but strongly detected in output")


class InferredTag(BaseModel):
    """Tag detected by tagger with confidence score."""
    tag: str
    score: float


class GenerationLog(BaseModel):
    """Generation log record for a single generation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique UUID for this generation")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of generation")
    user_action: Optional[str] = Field(default=None, description="User evaluation: 'keep' or 'discard'")
    prompt_tags: List[str] = Field(default_factory=list, description="Normalized tags specified during generation")
    inferred_tags: List[InferredTag] = Field(default_factory=list, description="Tags detected from generated image with confidence scores")
    mismatch_data: MismatchData = Field(default_factory=MismatchData, description="Mismatch information between input and output")
    info_text: str = Field(default="", description="Info text from generation")
    param: str = Field(default="{}", description="JSON stringified SDPEM generation parameters")


# ================================================================================
# B. Tag Stats Master Models
# ================================================================================

class TagCooccurrence(BaseModel):
    """Co-occurring tag with frequency."""
    tag: str
    frequency: int


class TagConflict(BaseModel):
    """Conflicting tag that reduces detection rate."""
    tag: str
    impact: float = Field(description="Negative impact on detection rate (0.0 to 1.0)")


class TagStats(BaseModel):
    """Statistics for a single tag."""
    tag_name: str
    usage_count: int = Field(default=0, description="Number of times this tag was used")
    detection_count: int = Field(default=0, description="Number of times this tag was detected in output")
    keep_count: int = Field(default=0, description="Number of times generations with this tag were kept")
    detection_rate: float = Field(default=0.0, description="(detection_count / usage_count) * 100")
    keep_rate: float = Field(default=0.0, description="(keep_count / usage_count) * 100")
    cooccurrence: List[TagCooccurrence] = Field(default_factory=list, description="Top N co-occurring tags")
    conflicts: List[TagConflict] = Field(default_factory=list, description="Tags that reduce detection rate")


# ================================================================================
# Generation Logger Class
# ================================================================================

class GenerationLogger:
    """Logger for generation records, saves to JSONL format."""
    
    def __init__(self, records_path: str = "assets/generation_records.jsonl"):
        """
        Initialize GenerationLogger.
        
        Args:
            records_path: Path to JSONL file for storing generation records.
                         Can be absolute or relative to project root.
        """
        # Convert to absolute path if relative
        if not os.path.isabs(records_path):
            self.records_path = str(PROJECT_ROOT / records_path)
        else:
            self.records_path = records_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the records file and its parent directory exist."""
        path = Path(self.records_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.touch()
    
    def save_log(
        self,
        prompt_tags: List[str],
        inferred_tags: List[Dict[str, float]],
        info_text: str,
        param: dict,
        user_action: Optional[str] = None,
        id: Optional[str] = None,
        timestamp: Optional[float] = None
    ) -> GenerationLog:
        """
        Save a generation log.
        
        Args:
            prompt_tags: List of normalized tags from input prompt
            inferred_tags: List of dicts with 'tag' and 'score' from tagger
            info_text: Info text from generation
            param: SDPEM generation parameters as dict
            user_action: Optional user action ('keep' or 'discard')
            id: Optional UUID (auto-generated if not provided)
            timestamp: Optional timestamp (auto-generated if not provided)
        
        Returns:
            GenerationLog object that was saved
        """
        # Convert inferred_tags to InferredTag objects
        inferred_tag_objects = [
            InferredTag(tag=tag_dict['tag'], score=tag_dict['score'])
            for tag_dict in inferred_tags
        ]
        
        # Calculate mismatch data
        inferred_tag_names = {tag.tag for tag in inferred_tag_objects}
        prompt_tag_set = set(prompt_tags)
        
        lost = [tag for tag in prompt_tags if tag not in inferred_tag_names]
        # Ghost tags are those with high confidence (>0.7) that weren't in input
        ghost = [
            tag.tag for tag in inferred_tag_objects
            if tag.tag not in prompt_tag_set and tag.score > 0.7
        ]
        
        mismatch = MismatchData(lost=lost, ghost=ghost)
        
        # Create log entry
        log_entry = GenerationLog(
            id=id if id else str(uuid.uuid4()),
            timestamp=timestamp if timestamp is not None else time.time(),
            user_action=user_action,
            prompt_tags=prompt_tags,
            inferred_tags=inferred_tag_objects,
            mismatch_data=mismatch,
            info_text=info_text,
            param=json.dumps(param, ensure_ascii=False)
        )
        
        # Append to JSONL file
        with open(self.records_path, 'a', encoding='utf-8') as f:
            f.write(log_entry.model_dump_json(ensure_ascii=False) + '\n')
        
        return log_entry
    
    def read_logs(self, limit: Optional[int] = None) -> List[GenerationLog]:
        """
        Read generation logs from JSONL file.
        
        Args:
            limit: Maximum number of logs to read (None for all)
        
        Returns:
            List of GenerationLog objects
        """
        logs = []
        if not Path(self.records_path).exists():
            return logs
        
        with open(self.records_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    break
                if line.strip():
                    try:
                        logs.append(GenerationLog.model_validate_json(line))
                    except Exception as e:
                        print(f"Error parsing log line {i}: {e}")
        
        return logs


# ================================================================================
# Tag Stats Manager Class
# ================================================================================

class TagStatsManager:
    """Manager for tag statistics, saves to individual JSON files."""
    
    def __init__(self, stats_dir: str = "assets/tag_stats"):
        """
        Initialize TagStatsManager.
        
        Args:
            stats_dir: Directory path for storing tag statistics JSON files.
                      Can be absolute or relative to project root.
        """
        # Convert to absolute path if relative
        if not os.path.isabs(stats_dir):
            self.stats_dir = str(PROJECT_ROOT / stats_dir)
        else:
            self.stats_dir = stats_dir
        self._ensure_dir_exists()
    
    def _ensure_dir_exists(self):
        """Ensure the stats directory exists."""
        Path(self.stats_dir).mkdir(parents=True, exist_ok=True)
    
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
        # Track which tags were detected
        detected_tags = {tag.tag for tag in log.inferred_tags if tag.score > 0.5}
        
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
