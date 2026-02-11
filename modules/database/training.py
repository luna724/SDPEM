import sys
import os
import math
import torch
from pathlib import Path

# Add project root to path when running as standalone script
if __name__ == "__main__":
  sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.database.preprocessing import PreProcessor
from modules.database.matrix import CooccurrenceMatrix
from modules.database.conflict import ConflictMap
from typing import Optional
from logger import info, warn
from modules.config import get_config

def calculate_avail_processes(model_size: float = 1.35, inference_vram: float = 0.3, reserve: float = 1.5) -> int:
  """Available VRAM/CPUから安全な並列数を見積もるため。"""
  try:
    cfg = get_config()
    device = getattr(cfg, "booru_device", "cpu")
    mem_limit_mb = getattr(cfg, "booru_cuda_inference_memory_limit", 0)
  except Exception:
    device = "cpu"
    mem_limit_mb = 0

  if device != "cuda":
    cpu_count = os.cpu_count() or 1
    return max(1, cpu_count - 2)

  free_gb = 0.0
  try:
    if torch.cuda.is_available():
      free_bytes, _ = torch.cuda.mem_get_info()
      free_gb = free_bytes / (1024 ** 3)
  except Exception:
    free_gb = 0.0

  if mem_limit_mb and mem_limit_mb > 0:
    free_gb = min(free_gb, mem_limit_mb / 1024)

  usable_gb = max(0.0, free_gb - reserve - model_size)
  max_proc = math.floor(usable_gb / inference_vram) if inference_vram > 0 else 1
  return max(1, max_proc)

async def train(
  pth: os.PathLike, 
  walkdir: bool = False,
  output_dir: Optional[os.PathLike] = None,
  min_conflict_occurrences: int = 250,
  conflict_confidence: float = 0.7,
  processes: int = calculate_avail_processes(), # 1.5(safe) + 1.35(model) + 0.3(infer) * proc (GB) # todo: 余ってるvramから自動計算
) -> dict:
  """
  Train the database system on image data.
  
  Workflow (as per docs/database.md):
  1. PreProcessor: Extract prompts, ratings, booru results from images
  2. CooccurrenceMatrix: Build co-occurrence matrices from prompts
  3. ConflictMap: Detect conflicts using co-occurrence data
  4. Save all generated matrices
  
  Args:
    pth: Path to directory containing images
    walkdir: If True, recursively process subdirectories
    output_dir: Directory to save matrices (default: data/)
    min_conflict_occurrences: Minimum tag occurrences for conflict detection
    conflict_confidence: Minimum confidence for auto-detected conflicts
  
  Returns:
    Dictionary with statistics and file paths
  """
  pth = Path(pth)
  if output_dir is None:
    output_dir = Path("data")
  else:
    output_dir = Path(output_dir)
  
  output_dir.mkdir(parents=True, exist_ok=True)
  
  info(f"Starting database training on: {pth}")
  
  # === Step 1: PreProcessor ===
  info("Step 1/3: Preprocessing images...")
  
  directories = []
  if walkdir:
    # Recursively find all directories with PNG files
    for root, dirs, files in os.walk(pth):
      if any(f.lower().endswith('.png') for f in files):
        directories.append(root)
    info(f"Found {len(directories)} directories with images")
  else:
    directories = [pth]
  
  all_prompts = []
  all_booru_inferred = []
  all_ratings = []
  
  for directory in directories:
    info(f"Processing directory: {directory}")
    preprocessor = PreProcessor(directory, "WD1.4 Vit Tagger v3 (large)")
    pool = await preprocessor.prepare(processes)
    
    # pool = [prompts, booru_inferred, ratings]
    all_prompts.extend(pool[0])
    all_booru_inferred.extend(pool[1])
    all_ratings.extend(pool[2])
  
  total_samples = len(all_prompts)
  info(f"Preprocessing complete. Total samples: {total_samples}")
  
  if total_samples == 0:
    warn("No valid samples found. Training aborted.")
    return {"status": "error", "message": "No valid samples"}
  
  # === Step 2: CooccurrenceMatrix ===
  info("Step 2/3: Building co-occurrence matrices...")
  
  # Build prompt matrix
  info("  - Building prompt co-occurrence matrix...")
  comtx = CooccurrenceMatrix.build_cls(
    tag_lists=all_prompts,
    rating=all_ratings,
    min_sample=min_conflict_occurrences
  )
  b_comtx = CooccurrenceMatrix.build_cls(
    tag_lists=all_booru_inferred,
    rating=all_ratings,
    min_sample=min_conflict_occurrences
  )
  
  info(f"  Prompt tags: {len(comtx.counts)}")
  info(f"  LoRA triggers found: {len(comtx.lora_matrix)}")
  
  # === Step 3: ConflictMap ===
  info("Step 3/3: Detecting tag conflicts...")
  
  # Start with base conflicts to merge auto-detected rules.
  conflict_map = ConflictMap()
  initial_conflicts = len(conflict_map.conflicts)
  info(f"  - Base conflicts: {initial_conflicts} tags")
  
  # Auto-detect conflicts from prompt data
  info(f"  - Auto-detecting conflicts (min_occurrences={min_conflict_occurrences}, confidence={conflict_confidence})...")
  conflict_map, detected = ConflictMap.auto_detect_conflicts(
    matrix=comtx,
    tag_counts=comtx.counts,
    total_documents=total_samples,
    min_occurrences=min_conflict_occurrences,
    min_confidence=conflict_confidence,
    merge_with_existing=True,
    base_map=conflict_map
  )
  
  info(f"  - Detected {len(detected)} new conflicts")
  info(f"  - Total conflicts: {len(conflict_map.conflicts)} tags")
  
  # === Step 4: Save everything ===
  info("Saving matrices and maps...",)
  
  # Save prompt matrix
  prompt_matrix_path = output_dir / "prompt_cooccurrence.json"
  comtx.to_file(prompt_matrix_path)
  
  # Save booru matrix
  booru_matrix_path = output_dir / "booru_matrix.json"
  b_comtx.to_file(booru_matrix_path)
  
  # Save conflict map
  conflict_map_path = output_dir / "conflict_map.json"
  conflict_map.to_file(conflict_map_path)
  
  # === Summary ===
  info("=" * 60)
  info("Training complete!")
  info(f"  Total samples: {total_samples}")
  info(f"  Unique tags: {len(comtx.counts)}")
  info(f"  LoRA triggers: {len(comtx.lora_matrix)}")
  info(f"  Conflicts detected: {len(detected)}")
  info(f"  Output directory: {output_dir}")
  info("=" * 60)
  
  return {
    "status": "success",
    "total_samples": total_samples,
    "unique_tags": len(comtx.counts),
    "lora_triggers": len(comtx.lora_matrix),
    "conflicts_detected": len(detected),
    "files": {
      "prompt_matrix": str(prompt_matrix_path),
      "booru_matrix": str(booru_matrix_path),
      "conflict_map": str(conflict_map_path)
    }
  }


if __name__ == "__main__":
  import asyncio
  import test
  tasks = asyncio.run(test.setup())
  
  if len(sys.argv) < 2:
    print("Usage: python training.py <image_directory> [--walkdir]")
    print("Example: python training.py ./images --walkdir")
    sys.exit(1)
  
  target_path = sys.argv[1]
  walk_directories = "--walkdir" in sys.argv
  
  asyncio.run(train(target_path, walkdir=walk_directories))
  for task in tasks:
    task.cancel()
