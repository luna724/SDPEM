"""
Auto-Conflict Detection for SDPEM Database Module

This module implements automatic detection of conflicting tag pairs based on
statistical analysis of co-occurrence patterns.

Key Features:
- Suppression rate analysis (mutual exclusivity detection)
- Context similarity filtering (avoid false positives)
- Optional semantic opposition check (Word2Vec integration)
- Confidence scoring for detected conflicts
"""

from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from collections import defaultdict
import math
import json
from pathlib import Path

from modules.database.matrix import CooccurrenceMatrix


@dataclass
class DetectedConflict:
  """Represents an automatically detected conflict between two tags."""
  tag_a: str
  tag_b: str
  confidence: float
  suppression_a_given_b: float
  suppression_b_given_a: float
  context_similarity: float
  auto_detected: bool = True
  
  def __repr__(self):
    return (
      f"DetectedConflict({self.tag_a} ↔ {self.tag_b}, "
      f"confidence={self.confidence:.3f})"
    )


class HighConfidenceConflictDetector:
  def __init__(
    self,
    min_occurrences: int = 250,
    min_suppression: float = 0.15,
    context_sim_range: Tuple[float, float] = (0.25, 0.75),
    confidence_threshold: float = 0.7,
    word2vec_model: Optional[any] = None
  ):
    """
    Initialize conflict detector.
    
    Args:
      min_occurrences: Minimum tag occurrence count to consider (default: 250)
      min_suppression: Minimum suppression rate to qualify as conflict (default: 0.15)
      context_sim_range: Valid range for context similarity (default: 0.25-0.75)
      confidence_threshold: Minimum confidence to report conflict (default: 0.7)
      word2vec_model: Optional Word2Vec model for semantic analysis
    """
    self.min_occurrences = min_occurrences
    self.min_suppression = min_suppression
    self.context_sim_range = context_sim_range
    self.confidence_threshold = confidence_threshold
    self.word2vec_model = word2vec_model
  
  def detect_conflicts(
    self,
    matrix_data: Dict[str, Dict[str, float]],
    tag_counts: Dict[str, int],
    total_documents: int
  ) -> List[DetectedConflict]:
    """
    Detect all conflicting tag pairs from co-occurrence matrix.
    
    Args:
      matrix_data: Co-occurrence matrix {tag_a: {tag_b: score}}
      tag_counts: Tag occurrence counts {tag: count}
      total_documents: Total number of documents/samples
    
    Returns:
      List of detected conflicts sorted by confidence (descending)
    """
    # Filter tags by minimum occurrences
    valid_tags = [
      tag for tag, count in tag_counts.items() 
      if count >= self.min_occurrences
    ]
    
    conflicts = []
    checked_pairs: Set[Tuple[str, str]] = set()
    
    # Check all pairs of valid tags
    for i, tag_a in enumerate(valid_tags):
      for tag_b in valid_tags[i + 1:]:
        # Avoid duplicate checks
        pair = tuple(sorted([tag_a, tag_b]))
        if pair in checked_pairs:
          continue
        checked_pairs.add(pair)
        
        # Detect conflict between this pair
        conflict = self._detect_pair(
          tag_a, tag_b,
          matrix_data,
          tag_counts,
          total_documents
        )
        
        if conflict is not None:
          conflicts.append(conflict)
    
    # Sort by confidence (highest first)
    conflicts.sort(key=lambda c: c.confidence, reverse=True)
    return conflicts
  
  def _detect_pair(
    self,
    tag_a: str,
    tag_b: str,
    matrix_data: Dict[str, Dict[str, float]],
    tag_counts: Dict[str, int],
    total_documents: int
  ) -> Optional[DetectedConflict]:
    """
    Detect if a specific tag pair is conflicting.
    
    Args:
      tag_a: First tag
      tag_b: Second tag
      matrix_data: Co-occurrence matrix
      tag_counts: Tag occurrence counts
      total_documents: Total number of documents
    
    Returns:
      DetectedConflict if conflict detected, None otherwise
    """
    # Stage 0: Check minimum occurrences (already filtered, but double-check)
    if tag_counts.get(tag_a, 0) < self.min_occurrences:
      return None
    if tag_counts.get(tag_b, 0) < self.min_occurrences:
      return None
    
    # Stage 1: Calculate suppression rate (必須)
    supp_b_given_a = self._suppression_rate(
      tag_b, tag_a, matrix_data, tag_counts, total_documents
    )
    supp_a_given_b = self._suppression_rate(
      tag_a, tag_b, matrix_data, tag_counts, total_documents
    )
    
    # Both directions must show significant suppression
    if supp_b_given_a < self.min_suppression or supp_a_given_b < self.min_suppression:
      return None
    
    # Stage 2: Calculate context similarity (必須)
    context_sim = self._context_similarity(tag_a, tag_b, matrix_data)
    
    # Filter by context similarity range
    min_sim, max_sim = self.context_sim_range
    if context_sim < min_sim:
      return None  # Different contexts, not conflicting
    if context_sim > max_sim:
      return None  # Too similar (likely synonyms), not conflicting
    
    # Stage 3: Semantic opposition check (任意)
    semantic_opposition = 0.0
    if self.word2vec_model is not None:
      semantic_opposition = self._semantic_check(tag_a, tag_b)
    
    # Calculate confidence score
    confidence = self._calculate_confidence(
      supp_b_given_a,
      supp_a_given_b,
      context_sim,
      semantic_opposition
    )
    
    # Return conflict if confidence exceeds threshold
    if confidence >= self.confidence_threshold:
      return DetectedConflict(
        tag_a=tag_a,
        tag_b=tag_b,
        confidence=confidence,
        suppression_a_given_b=supp_a_given_b,
        suppression_b_given_a=supp_b_given_a,
        context_similarity=context_sim,
        auto_detected=True
      )
    
    return None
  
  def _suppression_rate(
    self,
    tag_b: str,
    tag_a: str,
    matrix_data: Dict[str, Dict[str, float]],
    tag_counts: Dict[str, int],
    total_documents: int
  ) -> float:
    """
    Calculate suppression rate: how much tag_a suppresses tag_b.
    
    Formula:
      supp(B|A) = P(B|¬A) - P(B|A)
    
    Where:
      P(B|A) = co-occurrence count / count(A)
      P(B|¬A) = (count(B) - co-occurrence) / (total - count(A))
    
    High suppression means B appears less when A is present.
    
    Args:
      tag_b: Tag being suppressed
      tag_a: Tag doing the suppressing
      matrix_data: Co-occurrence matrix
      tag_counts: Tag counts
      total_documents: Total documents
    
    Returns:
      Suppression rate (0.0 to 1.0, higher = stronger suppression)
    """
    count_a = tag_counts.get(tag_a, 0)
    count_b = tag_counts.get(tag_b, 0)
    
    if count_a == 0 or count_b == 0:
      return 0.0
    
    # Get co-occurrence count
    # Note: matrix_data uses PMI scores, so we need to reconstruct counts
    # For simplicity, we'll use a heuristic: check raw co-occurrence
    cooccur_count = self._get_cooccurrence_count(
      tag_a, tag_b, matrix_data, tag_counts, total_documents
    )
    
    # P(B|A) = P(A, B) / P(A)
    p_b_given_a = cooccur_count / count_a if count_a > 0 else 0.0
    
    # P(B|¬A) = (count(B) - cooccur) / (total - count(A))
    count_not_a = total_documents - count_a
    if count_not_a == 0:
      return 0.0
    
    p_b_given_not_a = (count_b - cooccur_count) / count_not_a
    
    # Suppression rate
    suppression = max(0.0, p_b_given_not_a - p_b_given_a)
    
    return suppression
  
  def _get_cooccurrence_count(
    self,
    tag_a: str,
    tag_b: str,
    matrix_data: Dict[str, Dict[str, float]],
    tag_counts: Dict[str, int],
    total_documents: int
  ) -> int:
    """
    Estimate co-occurrence count from PMI matrix.
    
    From PMI formula:
      PMI = log(P(A,B) / (P(A) * P(B)))
      => P(A,B) = exp(PMI) * P(A) * P(B)
      => count(A,B) = P(A,B) * total
    
    Args:
      tag_a: First tag
      tag_b: Second tag
      matrix_data: PMI matrix
      tag_counts: Tag counts
      total_documents: Total documents
    
    Returns:
      Estimated co-occurrence count
    """
    pmi = matrix_data.get(tag_a, {}).get(tag_b, 0.0)
    
    if pmi == 0.0:
      # Try reverse direction
      pmi = matrix_data.get(tag_b, {}).get(tag_a, 0.0)
    
    if pmi == 0.0:
      return 0  # No co-occurrence data
    
    # Reconstruct P(A,B) from PMI
    p_a = tag_counts.get(tag_a, 0) / total_documents
    p_b = tag_counts.get(tag_b, 0) / total_documents
    
    # PMI = log(P(A,B) / (P(A) * P(B)))
    # P(A,B) = exp(PMI) * P(A) * P(B)
    p_ab = math.exp(pmi) * p_a * p_b
    
    count_ab = int(p_ab * total_documents)
    
    # Clamp to valid range
    count_ab = max(0, min(count_ab, min(tag_counts.get(tag_a, 0), tag_counts.get(tag_b, 0))))
    
    return count_ab
  
  def _context_similarity(
    self,
    tag_a: str,
    tag_b: str,
    matrix_data: Dict[str, Dict[str, float]]
  ) -> float:
    """
    Calculate context similarity using weighted Jaccard similarity.
    
    Context = set of tags that co-occur with a given tag.
    High similarity = tags appear in similar contexts.
    
    Args:
      tag_a: First tag
      tag_b: Second tag
      matrix_data: Co-occurrence matrix
    
    Returns:
      Similarity score (0.0 to 1.0)
    """
    # Get co-occurrence contexts (using PMI scores as weights)
    context_a = matrix_data.get(tag_a, {})
    context_b = matrix_data.get(tag_b, {})
    
    if not context_a or not context_b:
      return 0.0
    
    # Weighted Jaccard similarity
    all_tags = set(context_a.keys()) | set(context_b.keys())
    
    intersection = sum(
      min(context_a.get(tag, 0.0), context_b.get(tag, 0.0))
      for tag in all_tags
    )
    
    union = sum(
      max(context_a.get(tag, 0.0), context_b.get(tag, 0.0))
      for tag in all_tags
    )
    
    if union == 0.0:
      return 0.0
    
    return intersection / union
  
  def _semantic_check(self, tag_a: str, tag_b: str) -> float:
    """
    Check semantic opposition using Word2Vec.
    
    Args:
      tag_a: First tag
      tag_b: Second tag
    
    Returns:
      Opposition score (0.0 to 1.0, higher = more opposed)
    """
    if self.word2vec_model is None:
      return 0.0
    
    try:
      # Get word vectors
      vec_a = self.word2vec_model.wv[tag_a]
      vec_b = self.word2vec_model.wv[tag_b]
      
      # Calculate cosine similarity
      from numpy import dot
      from numpy.linalg import norm
      
      cosine_sim = dot(vec_a, vec_b) / (norm(vec_a) * norm(vec_b))
      
      # Opposition = 1 - similarity (negative similarity = opposition)
      # Map [-1, 1] to [0, 1] where 1 = highly opposed, 0 = similar
      opposition = (1.0 - cosine_sim) / 2.0
      
      return opposition
    
    except KeyError:
      # Tags not in vocabulary
      return 0.0
  
  def _context_appropriateness(self, context_sim: float) -> float:
    """
    Score how appropriate the context similarity is for conflicts.
    
    Optimal range: medium similarity (same domain but exclusive)
    Too low: different domains
    Too high: synonyms
    
    Args:
      context_sim: Context similarity score
    
    Returns:
      Appropriateness score (0.0 to 1.0)
    """
    min_sim, max_sim = self.context_sim_range
    optimal_sim = (min_sim + max_sim) / 2.0
    
    # Distance from optimal point
    distance = abs(context_sim - optimal_sim)
    max_distance = (max_sim - min_sim) / 2.0
    
    # Convert to appropriateness (closer to optimal = higher score)
    appropriateness = 1.0 - (distance / max_distance) if max_distance > 0 else 1.0
    
    return appropriateness
  
  def _calculate_confidence(
    self,
    supp_b_given_a: float,
    supp_a_given_b: float,
    context_sim: float,
    semantic_opposition: float
  ) -> float:
    """
    Calculate overall confidence score for conflict detection.
    
    Weighted combination of:
    - Suppression strength (50%): how much tags suppress each other
    - Context appropriateness (30%): medium similarity is ideal
    - Semantic opposition (20%): Word2Vec-based semantic conflict
    
    Args:
      supp_b_given_a: Suppression rate of B given A
      supp_a_given_b: Suppression rate of A given B
      context_sim: Context similarity
      semantic_opposition: Semantic opposition score
    
    Returns:
      Confidence score (0.0 to 1.0)
    """
    # Suppression strength: use minimum (both must be high)
    suppression_strength = min(supp_b_given_a, supp_a_given_b)
    
    # Context appropriateness
    context_score = self._context_appropriateness(context_sim)
    
    # Weighted combination
    confidence = (
      0.5 * suppression_strength +
      0.3 * context_score +
      0.2 * semantic_opposition
    )
    
    return confidence

class ConflictMap:
    def __init__(self, conflicts: Optional[Dict[str, List[str]]] = None):
        """
        Initialize conflict map.

        Args:
            conflicts: Dictionary of {tag: [conflicting_tags]}
        """
        self.conflicts: Dict[str, Set[str]] = {}
        if conflicts:
            for tag, conflict_list in conflicts.items():
                self.conflicts[tag] = set(conflict_list)

    @classmethod
    def from_file(cls, path: Path) -> 'ConflictMap':
        """Load conflict map from JSON file."""
        if not path.exists(): raise FileNotFoundError(f"Conflict map not found at {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)

    def to_file(self, path: Path):
        """Save conflict map to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Convert sets to lists for JSON serialization
        data = {tag: list(conflicts) for tag, conflicts in self.conflicts.items()}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_conflict(self, tag_a: str, tag_b: str):
        """
        Add bidirectional conflict between two tags.
        
        Args:
            tag_a: First tag
            tag_b: Second tag
        """
        if tag_a not in self.conflicts:
            self.conflicts[tag_a] = set()
        if tag_b not in self.conflicts:
            self.conflicts[tag_b] = set()
        
        self.conflicts[tag_a].add(tag_b)
        self.conflicts[tag_b].add(tag_a)
    
    def has_conflict(self, existing_tags: Set[str], new_tag: str) -> bool:
        """
        Check if adding new_tag conflicts with existing tags.
        
        Args:
            existing_tags: Set of tags already in the prompt
            new_tag: Tag to check
        
        Returns:
            True if conflict exists, False otherwise
        """
        if new_tag not in self.conflicts:
            return False
        
        conflicting_tags = self.conflicts[new_tag]
        return bool(existing_tags & conflicting_tags)
    
    @classmethod
    def auto_detect_conflicts(
        cls,
        matrix: 'CooccurrenceMatrix',
        tag_counts: dict[str, int],
        total_documents: int,
        min_occurrences: int = 250,
        min_confidence: float = 0.7,
        word2vec_model: Optional[any] = None,
        merge_with_existing: bool = True,
        base_map: Optional['ConflictMap'] = None
    ) -> tuple['ConflictMap', list[tuple[str, str, float]]]:
        """
        Automatically detect conflicting tag pairs from co-occurrence data.

        Uses statistical analysis to identify tags that:
        - Rarely appear together despite high individual frequency
        - Have similar contexts (same domain)
        - Are mutually exclusive in practice

        Args:
            matrix: CooccurrenceMatrix with tag co-occurrence data
            tag_counts: Dictionary of {tag: occurrence_count}
            total_documents: Total number of documents/prompts analyzed
            min_occurrences: Minimum tag count to consider (default: 250)
            min_confidence: Minimum confidence to add conflict (default: 0.7)
            word2vec_model: Optional Word2Vec model for semantic analysis
            merge_with_existing: If True, add detected conflicts to base_map
            base_map: Optional ConflictMap to merge into

        Returns:
            Tuple of (ConflictMap, detected conflicts list)
        """
        
        conflict_map = base_map if base_map is not None else cls()
        detector = HighConfidenceConflictDetector(
            min_occurrences=min_occurrences,
            confidence_threshold=min_confidence,
            word2vec_model=word2vec_model
        )

        detected = detector.detect_conflicts(
            matrix.matrix,
            tag_counts,
            total_documents
        )

        # Add to conflict map if requested
        results: list[tuple[str, str, float]] = []
        for conflict in detected:
            results.append((conflict.tag_a, conflict.tag_b, conflict.confidence))
            
            if merge_with_existing:
                conflict_map.add_conflict(conflict.tag_a, conflict.tag_b)

        return conflict_map, results
