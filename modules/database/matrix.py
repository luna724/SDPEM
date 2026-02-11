import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

LORA_TRIGGER_PATTERN = r"^<lora:(.*)?>"

def is_lora_trigger(tag: str) -> bool:
  """Check if a tag is a LoRA trigger (e.g., <lora:name:weight>)"""
  return re.match(LORA_TRIGGER_PATTERN, tag.strip()) is not None

class CooccurrenceMatrix:
    """Manages tag co-occurrence probabilities using PMI (Pointwise Mutual Information)"""
    
    def __init__(
      self,
      matrix: Dict[str, Dict[str, float]],
      counts: Dict[str, int],
      lora_matrix: Dict[str, Dict[str, float]],
      rating_matrix: Dict[str, Dict[str, float]],
      always_tag: List[str],
      lora_similarity_matrix: Optional[Dict[str, Dict[str, float]]],
      lora_conflict_matrix: Optional[Dict[str, Dict[str, float]]]
    ):
        self.matrix: Dict[str, Dict[str, float]] = matrix
        self.counts: Dict[str, int] = counts
        self.lora_matrix: Dict[str, Dict[str, float]] = lora_matrix
        self.rating_matrix: Dict[str, Dict[str, float]] = rating_matrix
        self.always_tag: List[str] = always_tag
        self.lora_similarity_matrix: Dict[str, Dict[str, float]] = lora_similarity_matrix
        self.lora_conflict_matrix: Dict[str, Dict[str, float]] = lora_conflict_matrix

    def get_related_tags(self, tag: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """
        Get tags most related to the given tag based on PMI scores.

        Args:
            tag: The tag to find related tags for
            top_k: Number of top related tags to return

        Returns:
            List of (tag, pmi_score) tuples sorted by PMI score (highest first)
        """
        if tag not in self.matrix:
            return []

        related = sorted(
            self.matrix[tag].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return related[:top_k]

    def get_probability(self, tag_a: str, tag_b: str) -> float:
        """
        Get the PMI score between two tags.
        Higher positive PMI = stronger positive association
        Negative PMI = negative association / mutual exclusion
        PMI around 0 = independent tags
        """
        if tag_a in self.matrix and tag_b in self.matrix[tag_a]:
            return self.matrix[tag_a][tag_b]
            return 0.0

    @classmethod
    def from_file(cls, path: Path) -> "CooccurrenceMatrix":
        """Load matrix from JSON file"""
        with open(path, "r", encoding="utf-8") as f:
          data = json.load(f)
        return cls(
            matrix=data.get("matrix", {}),
            counts=data.get("counts", {}),
            lora_matrix=data.get("lora_matrix", {}),
            rating_matrix=data.get("rating_matrix", {}),
            always_tag=data.get("always_tag", []),
            lora_similarity_matrix=data.get("lora_similarity_matrix", {}),
            lora_conflict_matrix=data.get("lora_conflict_matrix", {})
        )

    def to_file(self, path: Path) -> None:
        """Save matrix to JSON file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
              {
                "matrix": self.matrix,
                "counts": self.counts,
                "lora_matrix": self.lora_matrix,
                "rating_matrix": self.rating_matrix,
                "always_tag": self.always_tag,
                "lora_similarity_matrix": self.lora_similarity_matrix,
                "lora_conflict_matrix": self.lora_conflict_matrix
              }, 
              f, ensure_ascii=False, indent=2
            )
    
    @classmethod
    def build_cls(
      cls, tag_lists: list[list[str]], rating: list[str], min_sample: int = 250
    ):
      matrix_data, tag_counts, lora_matrix, always_tag = cls.create_matrix(tag_lists)
      rating_matrix = cls.create_rating_matrix(tag_lists, rating, min_sample)
      lora_similarity, lora_conflict = cls.create_lora_metrices(lora_matrix)
      
      return cls(
        matrix_data, tag_counts, lora_matrix, rating_matrix, always_tag,
        lora_similarity, lora_conflict
      )

    @staticmethod
    def create_matrix(tag_lists: List[List[str]]) -> tuple[dict[str, dict[str, float]], dict[str, int], dict[str, dict[str, float]], list[str]]:
        """
        Args:
          tag_lists: List of tag sets (e.g., from generation logs)

        Returns:
          Tuple of (co-occurrence matrix, tag counts, lora matrix)
        """
        # Count co-occurrences
        cooccur_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        total_documents = len(tag_lists)
        tag_counts: Dict[str, int] = defaultdict(int)
        matrix_data: Dict[str, Dict[str, float]] = {}
        lora_matrix: Dict[str, Dict[str, float]] = {}
        always_tag = []
        

        for tags in tag_lists:
          unique_tags = list(set(tags))  # Remove duplicates within a set

          for tag in unique_tags:
            tag_counts[tag] += 1
            for other_tag in unique_tags:
              if tag != other_tag:
                cooccur_counts[tag][other_tag] += 1

        # Calculate PMI scores
        for tag, others in cooccur_counts.items():
          p_tag = tag_counts[tag] / total_documents  # P(tag)

          # matrix_data[tag] = {}
          d = {}

          for other_tag, cooccur_count in others.items():
            p_other = tag_counts[other_tag] / total_documents  # P(other)
            p_together = cooccur_count / total_documents  # P(tag, other)

            # PMI = log(P(tag, other) / (P(tag) * P(other)))
            if p_tag > 0 and p_other > 0 and p_together > 0:
              pmi = math.log(p_together / (p_tag * p_other))

              # Normalize PMI to [0, 1] range using sigmoid-like transformation
              # Positive PMI = strong association, negative PMI = weak/negative association
              # We use max(0, pmi) to keep only positive associations
              # normalized_pmi = max(0.0, pmi)

              # matrix_data[tag][other_tag] = pmi
              d[other_tag] = pmi
          
          if len(d) > 0:
            d = {k: v for k, v in d.items() if v != 0}
            if len(d) == 0:
              always_tag.append(tag)
            else:
              if is_lora_trigger(tag):
                lora_matrix[tag] = d
              else:
                matrix_data[tag] = d
        
        
        return matrix_data, tag_counts, lora_matrix, always_tag

    @staticmethod
    def create_rating_matrix(
        tag_lists: list[list[str]], 
        each_ratings: list[str | int | float],
        min_sample: int = 250
    ) -> dict[str, dict[str, float]]:
        if len(tag_lists) != len(each_ratings):
            raise ValueError(
                f"tag_lists and each_ratings must have the same length: "
                f"{len(tag_lists)} != {len(each_ratings)}"
            )
        
        ratings_str = [str(r) for r in each_ratings]
        
        tag_counts: dict[str, int] = defaultdict(int)
        tag_rating_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for tags, rating in zip(tag_lists, ratings_str):
            unique_tags = list(set(tags))
            
            for tag in unique_tags:
                tag_counts[tag] += 1
                tag_rating_counts[tag][rating] += 1
        
        steering_matrix: dict[str, dict[str, float]] = {}
        
        for tag, rating_dict in tag_rating_counts.items():
            total_tag_count = tag_counts[tag]
            if total_tag_count < min_sample:
              continue
            
            steering_matrix[tag] = {}
            
            for rating, cooccur_count in rating_dict.items():
                probability = cooccur_count / total_tag_count
                steering_matrix[tag][rating] = probability
        
        return steering_matrix
    
    @staticmethod
    def create_lora_metrices(
        lora_matrix: Dict[str, Dict[str, float]]
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
        """
        Pre-calculate LoRA similarity and conflict matrices for persistence.
        
        This is computationally expensive, so we do it once during training
        and save the results to JSON.
        
        Args:
            lora_matrix: LoRA -> tag -> PMI associations
        
        Returns:
            Tuple of (lora_similarity_matrix, lora_conflict_matrix)
            - lora_similarity_matrix: lora_a -> lora_b -> similarity_score
            - lora_conflict_matrix: lora_a -> lora_b -> conflict_score
        """
        lora_list = list(lora_matrix.keys())
        
        # Helper: Calculate PPMI vector for a LoRA
        def get_ppmi_vector(lora: str) -> Dict[str, float]:
            if lora not in lora_matrix:
                return {}
            return {
                tag: max(0.0, pmi)
                for tag, pmi in lora_matrix[lora].items()
            }
        
        # Helper: Calculate L2 norm
        def get_vector_norm(ppmi_vector: Dict[str, float]) -> float:
            if not ppmi_vector:
                return 0.0
            return math.sqrt(sum(score ** 2 for score in ppmi_vector.values()))
        
        # Calculate all pairwise similarities and conflicts
        similarity_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        conflict_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        for i, lora_a in enumerate(lora_list):
            ppmi_a = get_ppmi_vector(lora_a)
            norm_a = get_vector_norm(ppmi_a)
            
            for lora_b in lora_list[i+1:]:
                ppmi_b = get_ppmi_vector(lora_b)
                norm_b = get_vector_norm(ppmi_b)
                
                # Calculate similarity (cosine similarity of PPMI vectors)
                similarity = 0.0
                if ppmi_a and ppmi_b and norm_a > 0 and norm_b > 0:
                    shared_tags = set(ppmi_a.keys()) & set(ppmi_b.keys())
                    dot_product = sum(ppmi_a[tag] * ppmi_b[tag] for tag in shared_tags)
                    similarity = max(0.0, min(1.0, dot_product / (norm_a * norm_b)))
                
                # Store bidirectionally
                similarity_matrix[lora_a][lora_b] = similarity
                similarity_matrix[lora_b][lora_a] = similarity
                
                # Calculate conflict (opposite associations)
                conflict_score = 0.0
                if lora_a in lora_matrix and lora_b in lora_matrix:
                    tags_a = lora_matrix[lora_a]
                    tags_b = lora_matrix[lora_b]
                    common_tags = set(tags_a.keys()) & set(tags_b.keys())
                    
                    conflicting_count = 0
                    total_conflict = 0.0
                    
                    for tag in common_tags:
                        pmi_a = tags_a[tag]
                        pmi_b = tags_b[tag]
                        
                        # Check for opposite associations
                        if (pmi_a > 0.5 and pmi_b < -0.5) or (pmi_a < -0.5 and pmi_b > 0.5):
                            total_conflict += abs(pmi_a - pmi_b) / 2.0
                            conflicting_count += 1
                    
                    if conflicting_count > 0:
                        conflict_score = min(1.0, total_conflict / conflicting_count)
                
                # Store bidirectionally
                conflict_matrix[lora_a][lora_b] = conflict_score
                conflict_matrix[lora_b][lora_a] = conflict_score
        
        # Convert defaultdicts to regular dicts for JSON serialization
        return dict(similarity_matrix), dict(conflict_matrix)
