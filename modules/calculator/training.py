import asyncio
import json
import sys
import os
import math
import torch
from pathlib import Path

# Add project root to path when running as standalone script
if __name__ == "__main__":
  sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.calculator.preprocessing import PreProcessor
from modules.calculator.matrix import CooccurrenceMatrix
from modules.calculator.conflict import ConflictMap
from typing import AsyncGenerator, Optional
from logger import info, warn
from modules.config import get_config

def calculate_avail_processes(model_size: float = 1.35, inference_vram: float = 0.4, reserve: float = 1.5) -> int:
  """Available VRAM/CPUから安全な並列数を見積もるため。"""
  try:
    cfg = get_config()
    device = getattr(cfg, "booru_device", "cpu")
  except Exception:
    device = "cpu"

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

  usable_gb = max(0.0, free_gb - reserve - model_size)
  max_proc = math.floor(usable_gb / inference_vram) if inference_vram > 0 else 1
  return max(1, max_proc)

def train_conflict(min_occr: int, confidence: float, matrix: dict, samples: int, exist_data: ConflictMap = None) -> dict:
  info(f"detecting conflicts (min_occurrences={min_occr}, confidence={confidence}, exist_data: {exist_data})...")
  
  if exist_data is None:
    exist_data = ConflictMap()
  if not isinstance(exist_data, ConflictMap):
    raise ValueError("exist_data must be a ConflictMap instance or None")
  r = ConflictMap.auto_detect_conflicts(
    matrix=matrix,
    tag_counts=matrix.counts,
    total_documents=samples,
    min_occurrences=min_occr,
    min_confidence=confidence,
    merge_with_existing=False,
    base_map=exist_data
  )
  return r

async def train(
  dataset_dir: list[os.PathLike | Path], 
  # dataset_dirは絶対パスである必要がある
  output: os.PathLike | Path,
  min_conflict_occurrences: int = 250,
  conflict_confidence: float = 0.7,
  processes: int = calculate_avail_processes(), # 1.5(safe) + 1.35(model) + 0.3(infer) * proc (GB)
  ignore_questionable: bool = True,
  booru_threshold: float = 0.45,
) -> AsyncGenerator[None, str]:
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
    output: Path to output file where metadata is saved
    min_conflict_occurrences: Minimum tag occurrences for conflict detection
    conflict_confidence: Minimum confidence for auto-detected conflicts
  
  Returns:
    Dictionary with statistics and file paths
  """
  yielded = ""
  def log(m):
    nonlocal yielded
    yielded += m + "\n"
    info(m)
    return yielded
  
  if not isinstance(output, Path):
    output = Path(output)
  output.parent.mkdir(parents=True, exist_ok=True)
  if processes <= -1:
    processes = calculate_avail_processes()
  processes = max(1, processes)
  yield log(f"Using {processes} parallel processes for training.")
  
  # === Step 1: PreProcessor ===
  yield log("Step 1/3: Preprocessing images...")
  
  all_prompts = []
  all_booru_inferred = []
  all_ratings = []
  
  if len(dataset_dir) == 0:
    yield log("No dataset directories specified. Training aborted.")
    return
  
  preprocessor = PreProcessor("WD1.4 Vit Tagger v3 (large)", ignore_questionable, booru_threshold=booru_threshold)

  # pool = [prompts, booru_inferred, ratings]
  pool = await preprocessor.prepare(
    [str(p) for p in dataset_dir],
    processes
  )
  
  all_prompts.extend(pool[0])
  all_booru_inferred.extend(pool[1])
  all_ratings.extend(pool[2])
  
  total_samples = len(all_prompts)
  yield log(f"Preprocessing complete. Total samples: {total_samples}")
  
  if total_samples == 0:
    yield log("No valid samples found. Training aborted.")
    return
  
  # === Step 2: CooccurrenceMatrix ===
  yield log("Step 2/3: Building co-occurrence matrices...")
  
  # Build prompt matrix
  yield log("  - Building prompt co-occurrence matrix...")
  comtx = await CooccurrenceMatrix.build_cls(
    tag_lists=all_prompts,
    rating=all_ratings,
    min_sample=min_conflict_occurrences
  )
  b_comtx = await CooccurrenceMatrix.build_cls(
    tag_lists=all_booru_inferred,
    rating=all_ratings,
    min_sample=min_conflict_occurrences
  )
  
  yield log(f"  Prompt tags: {len(comtx.counts)}")
  yield log(f"  LoRA triggers found: {len(comtx.lora_matrix)}")
  
  # === Step 3: ConflictMap ===
  yield log("Step 3/3: Detecting tag conflicts...")
  conflict_map = await asyncio.to_thread(train_conflict,
    min_occr=min_conflict_occurrences, 
    confidence=conflict_confidence, 
    matrix=comtx, 
    samples=total_samples
  )
  b_conf = await asyncio.to_thread(train_conflict, 
    min_occr=min_conflict_occurrences, 
    confidence=conflict_confidence, 
    matrix=b_comtx, 
    samples=total_samples
  )
  
  # === Step 4: Save everything ===
  yield log("Saving matrices and maps...")
  met = {}
  
  met["matrix"] = comtx.to_file(None, build_data=True)
  met["booru"] = b_comtx.to_file(None, build_data=True)
  
  met["matrix.conflict"] = conflict_map.to_file(None, build_data=True)
  met["booru.conflict"] = b_conf.to_file(None, build_data=True)
  
  with output.open("w", encoding="utf-8") as f:
    json.dump(met, f, ensure_ascii=False, separators=(",", ":"))
    
  yield log(f"Saved matrices to {output}")
  # === Summary ===
  yielded = ""
  yield log("=" * 60)
  yield log(f"  Total samples: {total_samples}")
  yield log(f"  Unique tags: {len(comtx.counts)}")
  yield log(f"  LoRA triggers: {len(comtx.lora_matrix)}")
  yield log(f"  Conflicts detected: {len(conflict_map.conflicts)}")
  yield log(f"  Booru conflicts detected: {len(b_conf.conflicts)}")
  yield log(f"  Output file: {output}")
  yield log("=" * 60)
  yield log("Training completed.")