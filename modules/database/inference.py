import math
import random
import re
from pathlib import Path

from logger import warn
from modules.database.conflict import ConflictMap
from modules.database.lora_asc import LoRAAssociation
from modules.database.matrix import CooccurrenceMatrix, is_lora_trigger
from modules.database.preprocessing import PreProcessor
from modules.database.similarity import SimilarityMatrix


class PromptInferenceEngine:
  """Co-occurrenceベースで追加タグを提案するための簡易推論エンジン。"""

  def __init__(self, data_dir: str | Path = "data"):
    self.data_dir = Path(data_dir)
    self.matrix_path = self.data_dir / "prompt_cooccurrence.json"
    self.conflict_path = self.data_dir / "conflict_map.json"

    self.matrix = CooccurrenceMatrix.from_file(self.matrix_path)
    self.conflict = self._load_conflicts()
    self.similarity = SimilarityMatrix.from_cooccurrence_matrix(self.matrix)
    self.lora = LoRAAssociation(self.matrix)

  def _load_conflicts(self) -> ConflictMap:
    try:
      return ConflictMap.from_file(self.conflict_path)
    except FileNotFoundError:
      warn(f"[PromptInference] conflict map missing at {self.conflict_path}, using empty map")
      return ConflictMap()

  @staticmethod
  def _normalize_tag(tag: str) -> str | None:
    norm = tag.strip()
    if not norm:
      return None

    if is_lora_trigger(norm):
      norm = re.sub(r"(<lora:[^:>]+):[^>]+>", r"\1>", norm)

    norm = norm.lower()
    norm = norm.replace("_", " ")
    norm = re.sub(r"(?<!\\):[0-9]+(?:\.[0-9]+)?$", "", norm)
    norm = re.sub(r"(?<!\\)[,:]+$", "", norm)
    norm = " ".join(norm.split())

    return norm if norm else None

  def _collect_candidates(self, current: set[str], top_k: int) -> dict[str, float]:
    candidates: dict[str, float] = {}

    for tag in current:
      related = self.matrix.get_related_tags(tag, top_k=top_k * 3)
      for cand, score in related:
        if score <= 0:
          continue
        if cand in current:
          continue
        candidates[cand] = candidates.get(cand, 0) + score

    return candidates

  def _apply_lora_boost(self, candidates: dict[str, float], active_loras: dict[str, float]) -> dict[str, float]:
    if not candidates or not active_loras:
      return candidates

    boosts = self.lora.get_boosted_tags(active_loras, list(candidates.keys()))
    adjusted: dict[str, float] = {}

    for tag, score in candidates.items():
      multiplier = boosts.get(tag, 1.0)
      adjusted[tag] = score * multiplier

    return adjusted

  def _filter_conflicts(self, candidates: dict[str, float], current: set[str]) -> dict[str, float]:
    filtered: dict[str, float] = {}

    for tag, score in candidates.items():
      if self.conflict.has_conflict(current, tag):
        continue
      filtered[tag] = score

    return filtered

  def _is_similar(self, tag: str, selected: list[str], threshold: float) -> bool:
    for existing in selected:
      if self.similarity.calculate_similarity(tag, existing) >= threshold:
        return True
    return False

  def _sample_candidates(
    self,
    candidates: dict[str, float],
    temperature: float,
    k: int,
    selected: list[str],
    similarity_threshold: float,
  ) -> list[str]:
    if not candidates:
      return []

    pool = dict(candidates)
    picks: list[str] = []
    temp = max(0.05, temperature)

    while pool and len(picks) < k:
      tags = list(pool.keys())
      scores = list(pool.values())
      max_score = max(scores)
      weights = [math.exp((s - max_score) / temp) for s in scores]

      choice = random.choices(tags, weights=weights, k=1)[0]

      if self.conflict.has_conflict(set(selected) | set(picks), choice):
        del pool[choice]
        continue

      if self._is_similar(choice, selected + picks, similarity_threshold):
        del pool[choice]
        continue

      picks.append(choice)
      del pool[choice]

    return picks
  
  def get_lora_weight(self, lora: str) -> float:
    m = re.compile(r"<lora:([^>]+)>").fullmatch(lora.strip())
    if not m or m.group(1).count(":") <= 0:
      return 1.0
    
    weights = ":".join(m.group(1).split(":")[1:])
    w = 1.0
    try:
      w = float(weights)
      return w
    except ValueError:
      pass
    for weight in weights:
      try:
        we = float(weight)
        w *= we
      except ValueError:
        continue
    return w

  def generate_prompt(
    self,
    init_tags: list[str],
    temperature: float = 1.0,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
  ) -> list[str]:
    active_loras: dict[str, float] = {}
    for t in init_tags:
      if not is_lora_trigger(t):
        continue
      norm = PreProcessor.normalize_tag(t)
      if norm is None:
        continue
      active_loras[norm] = self.get_lora_weight(t)

    normalized = PreProcessor.seprompt(init_tags)

    if not normalized or len(normalized) == 0:
      return []

    base_set = list(dict.fromkeys(normalized))

    for tag in self.matrix.always_tag:
      if tag not in base_set and not self.conflict.has_conflict(set(base_set), tag):
        base_set.append(tag)

    candidate_scores = self._collect_candidates(set(base_set), max(1, top_k))
    candidate_scores = self._apply_lora_boost(candidate_scores, active_loras)
    candidate_scores = self._filter_conflicts(candidate_scores, set(base_set))

    picks = self._sample_candidates(
      candidate_scores,
      temperature=temperature,
      k=max(1, top_k),
      selected=base_set,
      similarity_threshold=similarity_threshold,
    )

    return base_set + picks

  def generate_prompt_text(
    self,
    init_tags: list[str],
    temperature: float = 1.0,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
  ) -> str:
    tags = self.generate_prompt(init_tags, temperature, top_k, similarity_threshold)
    return ", ".join(tags)


def load_default_engine() -> PromptInferenceEngine:
  """data/ 配下の学習済みマトリクスで推論するためのヘルパー。"""
  data_root = Path("data")
  if not data_root.exists():
    raise FileNotFoundError("data directory not found; run training first")
  return PromptInferenceEngine(data_root)


__all__ = ["PromptInferenceEngine", "load_default_engine"]
