import json
import math
import random
import re
from pathlib import Path
from typing import Literal

from logger import warn
from modules.calculator.conflict import ConflictMap
from modules.calculator.lora_asc import LoRAAssociation
from modules.calculator.matrix import CooccurrenceMatrix, is_lora_trigger
from modules.calculator.preprocessing import PreProcessor
from modules.calculator.similarity import SimilarityMatrix


class PromptInferenceEngine:
  """Co-occurrenceベースで追加タグを提案するための簡易推論エンジン。"""

  def __init__(self, data_dir: str | Path, base: Literal["matrix", "booru"] = "matrix"):
    self.data_dir = Path(data_dir)
    if not self.data_dir.exists():
      raise FileNotFoundError(f"data directory not found at {self.data_dir}; run training first")

    with open(self.data_dir, "r", encoding="utf-8") as f:
      data = json.load(f)
    
    self.matrix = CooccurrenceMatrix.from_file(data[base])
    self.conflict = ConflictMap.from_file(data[base+".conflict"])
    self.similarity = SimilarityMatrix.from_cooccurrence_matrix(self.matrix)
    self.lora = LoRAAssociation(self.matrix)
    
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

  def _apply_rating_bias(self, candidates: dict[str, float], target_rating: str, force_rating: float, strength: float) -> dict[str, float]:
    if not candidates or strength <= 0:
      return candidates

    biased: dict[str, float] = {}

    for tag, score in candidates.items():
      rating_prob = self.matrix.rating_matrix.get(tag, {}).get(str(target_rating), 0.0)
      multiplier = 1.0 + (rating_prob - force_rating) * strength
      biased[tag] = score * multiplier

    return biased

  def _filter_conflicts(self, candidates: dict[str, float], current: set[str], negatives: set[str]) -> dict[str, float]:
    filtered: dict[str, float] = {}

    for tag, score in candidates.items():
      if tag in negatives:
        continue
      if self.conflict.has_conflict(current, tag):
        continue
      if self.conflict.has_conflict(negatives, tag):
        continue
      filtered[tag] = score

    return filtered

  def _is_similar(self, tag: str, selected: list[str], threshold: float) -> bool:
    for existing in selected:
      if self.similarity.calculate_similarity(tag, existing) >= threshold:
        return True
    return False

  def _apply_negative_penalty(
    self,
    candidates: dict[str, float],
    negatives: set[str],
    strength: float,
    threshold: float,
  ) -> dict[str, float]:
    if not candidates or not negatives:
      return candidates

    adjusted: dict[str, float] = {}

    for tag, score in candidates.items():
      if tag in negatives:
        continue

      # 3. 高速化: 共通するネガティブタグだけを抽出 (Set Intersection)
      # ループ回数を劇的に減らせる
      common_negatives = negatives.intersection(self.matrix.matrix.get(tag, {}).keys())
      
      if not common_negatives:
        # ネガティブ要素との関連が一切なければスコアはそのまま
        adjusted[tag] = score
        continue

      max_pmi = 0.0
      for neg in common_negatives:
        pmi = self.matrix.matrix.get(tag, {}).get(neg, 0.0)
        max_pmi = max(max_pmi, pmi)

      if max_pmi < threshold:
        adjusted[tag] = score
        continue

      if strength == float("inf"):
        if max_pmi > 0:
          continue
        penalty = 1.0
      else:
        penalty = 1.0 + max(0.0, max_pmi) * strength

      if not math.isfinite(penalty) or penalty <= 0:
        continue

      adjusted[tag] = score / penalty

    return adjusted

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
      weight_pairs = []
      for tag, score in zip(tags, scores):
        w = math.exp((score - max_score) / temp)
        if math.isfinite(w) and w > 0:
          weight_pairs.append((tag, w))

      if not weight_pairs:
        break

      tags, weights = zip(*weight_pairs)

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
    init_negatives: list[str] = ["worst quality", "1boy"],
    temperature: float = 1.0,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
    target_rating: Literal["general", "sensitive", "explicit"] = "general",
    rating_strength: float = 1.0,
    force_rating: float = 0.0,
    negative_strength: float = float("inf"),
    negative_threshold: float = 0.05,
    append_always_tags: bool = True,
  ) -> list[str]:
    original_init = list(dict.fromkeys(init_tags))
    active_loras: dict[str, float] = {}
    for t in init_tags:
      if not is_lora_trigger(t):
        continue
      norm = PreProcessor.normalize_tag(t)
      if norm is None:
        continue
      active_loras[norm] = self.get_lora_weight(t)

    normalized = PreProcessor.seprompt(init_tags)
    negative_tags = PreProcessor.seprompt(init_negatives)
    negative_set = set(negative_tags)

    if not normalized or len(normalized) == 0:
      return []

    base_set = list(dict.fromkeys(normalized))

    always_added: list[str] = []
    if append_always_tags:
      for tag in self.matrix.always_tag:
        if tag not in base_set and not self.conflict.has_conflict(set(base_set), tag):
          base_set.append(tag)
          always_added.append(tag)

    candidate_scores = self._collect_candidates(set(base_set), max(1, top_k))
    candidate_scores = self._apply_lora_boost(candidate_scores, active_loras)
    candidate_scores = self._apply_rating_bias(
      candidate_scores,
      target_rating,
      force_rating,
      rating_strength,
    )
    candidate_scores = self._apply_negative_penalty(
      candidate_scores,
      negative_set,
      negative_strength,
      negative_threshold,
    )
    candidate_scores = self._filter_conflicts(candidate_scores, set(base_set), negative_set)

    picks = self._sample_candidates(
      candidate_scores,
      temperature=temperature,
      k=max(1, top_k),
      selected=base_set,
      similarity_threshold=similarity_threshold,
    )

    combined = original_init + always_added + picks
    return combined

  def generate_prompt_text(
    self,
    init_tags: list[str],
    init_negatives: list[str] = ["worst quality", "1boy"],
    temperature: float = 1.0,
    top_k: int = 10,
    similarity_threshold: float = 0.7,
    target_rating: Literal["general", "sensitive", "explicit"] = "general",
    rating_strength: float = 1.0,
    force_rating: float = 0.0,
    negative_strength: float = float("inf"),
    negative_threshold: float = 0.05,
  ) -> str:
    tags = self.generate_prompt(
      init_tags,
      init_negatives=init_negatives,
      temperature=temperature,
      top_k=top_k,
      similarity_threshold=similarity_threshold,
      target_rating=target_rating,
      rating_strength=rating_strength,
      force_rating=force_rating,
      negative_strength=negative_strength,
      negative_threshold=negative_threshold,
    )
    return ", ".join(tags)


def load_default_engine() -> PromptInferenceEngine:
  """data/ 配下の学習済みマトリクスで推論するためのヘルパー。"""
  data_root = Path("data")
  if not data_root.exists():
    raise FileNotFoundError("data directory not found; run training first")
  return PromptInferenceEngine(data_root)


__all__ = ["PromptInferenceEngine", "load_default_engine"]
