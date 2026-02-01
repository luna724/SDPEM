"""
Example usage of the database logger module.

This example demonstrates how to use GenerationLogger and TagStatsManager
to record generation logs and manage tag statistics.
"""

from modules.database.logger import GenerationLogger, TagStatsManager

# ================================================================================
# Example 1: Basic Generation Logging
# ================================================================================

def example_generation_logging():
    """Example of logging a generation."""
    
    # Initialize the logger (uses default path: assets/generation_records.jsonl)
    logger = GenerationLogger()
    
    # Prepare data from a generation
    prompt_tags = ["1girl", "blonde_hair", "blue_eyes", "smile", "school_uniform"]
    
    # These would come from the tagger after generation
    inferred_tags = [
        {"tag": "1girl", "score": 0.95},
        {"tag": "blonde_hair", "score": 0.88},
        {"tag": "blue_eyes", "score": 0.82},
        {"tag": "smile", "score": 0.65},
        {"tag": "long_hair", "score": 0.78},  # Not in prompt (ghost tag)
        {"tag": "school_uniform", "score": 0.45},  # Low score, might be lost
    ]
    
    # Info text from the generation
    info_text = """Steps: 20, Sampler: DPM++ 2M Karras, CFG scale: 7.0, 
Seed: 1234567890, Size: 512x768, Model: anime_model_v3"""
    
    # Generation parameters
    param = {
        "prompt": "1girl, blonde hair, blue eyes, smile, school uniform",
        "negative_prompt": "bad quality, worst quality",
        "steps": 20,
        "cfg_scale": 7.0,
        "width": 512,
        "height": 768,
        "sampler": "DPM++ 2M Karras",
        "seed": 1234567890
    }
    
    # Save the log
    log = logger.save_log(
        prompt_tags=prompt_tags,
        inferred_tags=inferred_tags,
        info_text=info_text,
        param=param,
        user_action="keep"  # or "discard" or None
    )
    
    print(f"Saved generation log with ID: {log.id}")
    print(f"Lost tags: {log.mismatch_data.lost}")
    print(f"Ghost tags: {log.mismatch_data.ghost}")


# ================================================================================
# Example 2: Reading Generation Logs
# ================================================================================

def example_reading_logs():
    """Example of reading generation logs."""
    
    logger = GenerationLogger()
    
    # Read all logs
    all_logs = logger.read_logs()
    print(f"Total logs: {len(all_logs)}")
    
    # Read only last 10 logs
    recent_logs = logger.read_logs(limit=10)
    
    # Process logs
    for log in recent_logs:
        print(f"ID: {log.id}")
        print(f"Timestamp: {log.timestamp}")
        print(f"User Action: {log.user_action}")
        print(f"Prompt Tags: {', '.join(log.prompt_tags)}")
        print(f"Inferred Tags: {len(log.inferred_tags)}")
        print("---")


# ================================================================================
# Example 3: Managing Tag Statistics
# ================================================================================

def example_tag_statistics():
    """Example of managing tag statistics."""
    
    # Initialize the manager (uses default path: assets/tag_stats/)
    manager = TagStatsManager()
    
    # Load stats for a specific tag
    stats = manager.load_tag_stats("1girl")
    
    if stats:
        print(f"Tag: {stats.tag_name}")
        print(f"Usage Count: {stats.usage_count}")
        print(f"Detection Rate: {stats.detection_rate:.1f}%")
        print(f"Keep Rate: {stats.keep_rate:.1f}%")
        print(f"Top Co-occurring Tags:")
        for cooccur in stats.cooccurrence[:5]:
            print(f"  - {cooccur.tag}: {cooccur.frequency} times")
    else:
        print("No statistics found for this tag yet")


# ================================================================================
# Example 4: Updating Statistics from Logs
# ================================================================================

def example_update_statistics():
    """Example of updating statistics from generation logs."""
    
    logger = GenerationLogger()
    manager = TagStatsManager()
    
    # Read all logs
    logs = logger.read_logs()
    
    # Update statistics for all logs
    manager.batch_update_from_logs(logs)
    
    print(f"Updated statistics from {len(logs)} logs")
    
    # Or update from a single log
    # manager.update_from_log(single_log)


# ================================================================================
# Example 5: Integration with Generation System
# ================================================================================

def example_integration():
    """Example of integrating with the generation system."""
    
    logger = GenerationLogger()
    manager = TagStatsManager()
    
    # After a generation is complete:
    # 1. Extract tags from prompt
    prompt_tags = ["1girl", "red_hair", "green_eyes"]
    
    # 2. Run tagger on generated image
    # from modules.tagger.predictor import OnnxRuntimeTagger
    # tagger = OnnxRuntimeTagger("model_name")
    # general_res, character_res, rating = await tagger.predict(image, threshold=0.5, character_threshold=0.7)
    
    # Convert tagger results to format needed by logger
    # inferred_tags = [{"tag": tag, "score": score} for tag, score in general_res.items()]
    
    # Mock data for example
    inferred_tags = [
        {"tag": "1girl", "score": 0.92},
        {"tag": "red_hair", "score": 0.85},
        {"tag": "green_eyes", "score": 0.78},
    ]
    
    # 3. Save log
    log = logger.save_log(
        prompt_tags=prompt_tags,
        inferred_tags=inferred_tags,
        info_text="Generation info...",
        param={"steps": 20, "cfg": 7.0},
        user_action=None  # Will be updated later when user decides
    )
    
    # 4. Update statistics
    manager.update_from_log(log)
    
    print(f"Logged and updated statistics for generation {log.id}")


# ================================================================================
# Example 6: Custom Paths
# ================================================================================

def example_custom_paths():
    """Example using custom file paths."""
    
    # Use custom paths instead of defaults
    logger = GenerationLogger(records_path="/custom/path/records.jsonl")
    manager = TagStatsManager(stats_dir="/custom/path/tag_stats")
    
    # Use as normal
    log = logger.save_log(
        prompt_tags=["1girl"],
        inferred_tags=[{"tag": "1girl", "score": 0.9}],
        info_text="test",
        param={}
    )
    manager.update_from_log(log)


if __name__ == "__main__":
    # Run examples
    print("=" * 60)
    print("Database Logger Examples")
    print("=" * 60)
    
    # Uncomment to run specific examples:
    # example_generation_logging()
    # example_reading_logs()
    # example_tag_statistics()
    # example_update_statistics()
    # example_integration()
    # example_custom_paths()
