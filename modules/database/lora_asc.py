"""
LoRA Association Module

Manages LoRA-tag relationships and provides recommendations based on active LoRAs.

Features:
1. Recommend tags highly associated with specific LoRAs
2. Detect conflicts between multiple active LoRAs
3. Prioritize LoRA-related tags in prompt generation
"""

from typing import Dict, List, Set, Tuple, Optional
import re


class LoRAAssociation:
    """
    Manages associations between LoRA models and tags.
    
    Uses the lora_matrix from CooccurrenceMatrix to:
    - Find tags that work well with specific LoRAs
    - Detect conflicting LoRAs (negative associations)
    - Boost tag scores when relevant LoRAs are active
    - Detect LoRAs with similar usage patterns
    """
    
    def __init__(self, matrix_data):
        """
        Initialize LoRA Association manager.
        
        Args:
            matrix_data: CooccurrenceMatrix instance containing all matrix data
        """
        self.matrix_data = matrix_data
        
        # Quick access to commonly used data
        self.lora_matrix = matrix_data.lora_matrix
        self.tag_matrix = matrix_data.matrix
        
        # Use pre-calculated matrices as cache (if available)
        # These are treated as read-only caches
        self._similarity_cache = matrix_data.lora_similarity_matrix
        self._conflict_cache = matrix_data.lora_conflict_matrix
        
        # PPMI vector cache for on-demand calculations
        self._ppmi_cache: Dict[str, Dict[str, float]] = {}
        self._norm_cache: Dict[str, float] = {}
    
    
    def get_related_tags(
        self,
        lora_name: str,
        activation_tags: Optional[List[str]] = None,
        top_k: int = 20,
        min_score: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Get tags most associated with a specific LoRA.
        
        Args:
            lora_name: LoRA trigger (e.g., "<lora:character_name>")
            activation_tags: Already selected tags (to avoid redundancy)
            top_k: Maximum number of tags to return
            min_score: Minimum PMI score threshold
        
        Returns:
            List of (tag, pmi_score) tuples, sorted by score (highest first)
            
        Example:
            tags = lora.get_related_tags("<lora:Hoshino_Ichika>", top_k=10)
            # Returns: [("blue_eyes", 1.2), ("long_hair", 1.0), ...]
        """
        if lora_name not in self.lora_matrix:
            return []
        
        associations = self.lora_matrix[lora_name]
        activation_set = set(activation_tags or [])
        
        # Filter and sort
        filtered = [
            (tag, score)
            for tag, score in associations.items()
            if score >= min_score and tag not in activation_set
        ]
        
        # Sort by PMI score (highest first)
        filtered.sort(key=lambda x: x[1], reverse=True)
        
        return filtered[:top_k]
    
    def get_boosted_tags(
        self,
        active_loras: Dict[str, float],
        candidate_tags: List[str],
        boost_factor: float = 1.5
    ) -> Dict[str, float]:
        """
        Calculate boost scores for tags based on active LoRAs.
        
        Tags with positive associations to active LoRAs get boosted scores.
        Tags with negative associations get penalized.
        
        Args:
            active_loras: Dictionary of active LoRA triggers and their weights
            candidate_tags: Tags to calculate boosts for
            boost_factor: Multiplier for positive associations
        
        Returns:
            Dictionary mapping tag -> boost_multiplier
            - >1.0: Tag is recommended with this LoRA
            - 1.0: Tag is neutral
            - <1.0: Tag is discouraged with this LoRA
            
        Example:
            active = {"<lora:Hoshino_Ichika>": 1.0}
            candidates = ["blue_eyes", "red_eyes", "long_hair"]
            boosts = lora.get_boosted_tags(active, candidates)
            # {"blue_eyes": 2.5, "long_hair": 2.0, "red_eyes": 0.8}
        """
        boost_scores = {}
        
        for tag in candidate_tags:
            total_boost = 1.0
            
            for lora, weight in active_loras.items():
                if lora not in self.lora_matrix:
                    continue
                
                if tag in self.lora_matrix[lora]:
                    pmi = self.lora_matrix[lora][tag]
                    pmi *= weight
                    
                    if pmi > 0:
                        # Positive association: boost the tag
                        total_boost *= (1.0 + pmi * (boost_factor - 1.0))
                    elif pmi < 0:
                        # Negative association: penalize the tag
                        total_boost *= max(0.1, 1.0 + pmi * 0.5)
            
            
            
            boost_scores[tag] = total_boost
        
        return boost_scores
    
    def detect_lora_conflicts(
        self,
        lora_a: str,
        lora_b: str
    ) -> Tuple[float, List[str]]:
        """
        Detect conflicts between two LoRAs.
        
        Uses pre-calculated conflict matrix if available (from training),
        otherwise calculates on-demand.
        
        Conflicts are identified by:
        1. Tags with opposite associations (positive for A, negative for B)
        2. Overlap in strong associations (may cause style conflicts)
        
        Args:
            lora_a: First LoRA trigger
            lora_b: Second LoRA trigger
        
        Returns:
            Tuple of (conflict_score, conflicting_tags)
            - conflict_score: 0.0 (no conflict) to 1.0 (high conflict)
            - conflicting_tags: List of tags causing conflicts
        """
        # Use pre-calculated conflict matrix if available
        if lora_a in self._conflict_cache and lora_b in self._conflict_cache[lora_a]:
            return (self._conflict_cache[lora_a][lora_b], [])
        
        if lora_b in self._conflict_cache and lora_a in self._conflict_cache[lora_b]:
            return (self._conflict_cache[lora_b][lora_a], [])
        
        
        # Calculate on-demand (not in pre-calculated matrix)
        if lora_a not in self.lora_matrix or lora_b not in self.lora_matrix:
            return (0.0, [])
        
        tags_a = self.lora_matrix[lora_a]
        tags_b = self.lora_matrix[lora_b]
        
        conflicting_tags = []
        conflict_score = 0.0
        comparison_count = 0
        
        # Find tags that have opposite associations
        common_tags = set(tags_a.keys()) & set(tags_b.keys())
        
        for tag in common_tags:
            pmi_a = tags_a[tag]
            pmi_b = tags_b[tag]
            
            # Check for opposite associations
            if (pmi_a > 0.5 and pmi_b < -0.5) or (pmi_a < -0.5 and pmi_b > 0.5):
                conflicting_tags.append(tag)
                conflict_score += abs(pmi_a - pmi_b) / 2.0
                comparison_count += 1
        
        # Normalize conflict score
        if comparison_count > 0:
            conflict_score = min(1.0, conflict_score / comparison_count)
        
        return (conflict_score, conflicting_tags)

    
    def check_multi_lora_compatibility(
        self,
        active_loras: List[str],
        conflict_threshold: float = 0.6
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Check compatibility between multiple active LoRAs.
        
        Args:
            active_loras: List of active LoRA triggers
            conflict_threshold: Minimum conflict score to report
        
        Returns:
            Dictionary mapping LoRA pairs to conflict info
            {lora_a: [(conflicting_lora, conflict_score), ...]}
            
        Example:
            loras = ["<lora:A>", "<lora:B>", "<lora:C>"]
            conflicts = lora.check_multi_lora_compatibility(loras)
            # {"<lora:A>": [("<lora:B>", 0.75)], ...}
        """
        conflicts = {}
        
        for i, lora_a in enumerate(active_loras):
            lora_conflicts = []
            
            for lora_b in active_loras[i+1:]:
                conflict_score, _ = self.detect_lora_conflicts(lora_a, lora_b)
                
                if conflict_score >= conflict_threshold:
                    lora_conflicts.append((lora_b, conflict_score))
            
            if lora_conflicts:
                conflicts[lora_a] = lora_conflicts
        
        return conflicts
    
    def get_recommended_tags_for_loras(
        self,
        active_loras: List[str],
        current_tags: Set[str],
        top_k: int = 10,
        min_score: float = 0.3
    ) -> List[Tuple[str, float, List[str]]]:
        """
        Get recommended tags based on all active LoRAs.
        
        Aggregates recommendations from multiple LoRAs and ranks by combined score.
        
        Args:
            active_loras: List of active LoRA triggers
            current_tags: Tags already in the prompt
            top_k: Number of recommendations to return
            min_score: Minimum combined score
        
        Returns:
            List of (tag, combined_score, supporting_loras)
            - tag: Recommended tag
            - combined_score: Aggregate score from all LoRAs
            - supporting_loras: Which LoRAs support this tag
            
        Example:
            loras = ["<lora:A>", "<lora:B>"]
            current = {"1girl", "solo"}
            recs = lora.get_recommended_tags_for_loras(loras, current)
            # [("blue_eyes", 2.5, ["<lora:A>", "<lora:B>"]), ...]
        """
        tag_scores: Dict[str, float] = {}
        tag_lora_support: Dict[str, List[str]] = {}
        
        for lora in active_loras:
            if lora not in self.lora_matrix:
                continue
            
            for tag, pmi in self.lora_matrix[lora].items():
                if tag in current_tags or pmi <= 0:
                    continue
                
                if tag not in tag_scores:
                    tag_scores[tag] = 0.0
                    tag_lora_support[tag] = []
                
                tag_scores[tag] += pmi
                tag_lora_support[tag].append(lora)
        
        # Create results
        recommendations = [
            (tag, score, tag_lora_support[tag])
            for tag, score in tag_scores.items()
            if score >= min_score
        ]
        
        # Sort by combined score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_k]
    
    def _get_lora_ppmi_vector(self, lora: str) -> Dict[str, float]:
        """
        Get PPMI (Positive PMI) vector for a LoRA.
        
        The vector represents "which tags does this LoRA co-occur with?"
        Used for calculating LoRA-to-LoRA similarity.
        """
        if lora in self._lora_ppmi_cache:
            return self._lora_ppmi_cache[lora]
        
        if lora not in self.lora_matrix:
            self._lora_ppmi_cache[lora] = {}
            return {}
        
        # Convert PMI to PPMI (keep only positive associations)
        ppmi_vector = {
            tag: max(0.0, pmi_score)
            for tag, pmi_score in self.lora_matrix[lora].items()
        }
        
        self._lora_ppmi_cache[lora] = ppmi_vector
        return ppmi_vector
    
    def _get_lora_vector_norm(self, lora: str) -> float:
        """
        Calculate L2 norm of LoRA's PPMI vector.
        Used for cosine similarity calculation.
        """
        if lora in self._lora_norm_cache:
            return self._lora_norm_cache[lora]
        
        ppmi_vector = self._get_lora_ppmi_vector(lora)
        
        if not ppmi_vector:
            self._lora_norm_cache[lora] = 0.0
            return 0.0
        
        import math
        norm = math.sqrt(sum(score ** 2 for score in ppmi_vector.values()))
        self._lora_norm_cache[lora] = norm
        return norm
    
    def calculate_lora_similarity(self, lora_a: str, lora_b: str) -> float:
        """
        Calculate similarity between two LoRAs based on their usage patterns.
        
        **High similarity means**: Both LoRAs are used in similar contexts
        (similar tag associations). They may be:
        - Alternative versions of similar characters/styles
        - LoRAs for the same purpose (e.g., two different pose LoRAs)
        - Redundant when used together
        
        Method: Cosine similarity of PPMI tag association vectors
        
        Args:
            lora_a: First LoRA trigger
            lora_b: Second LoRA trigger
        
        Returns:
            Similarity score in range [0, 1]
            - 1.0 = extremely similar usage (may be redundant)
            - 0.0 = completely different usage
            
        Example:
            sim = lora.calculate_lora_similarity(
                "<lora:character_school>",
                "<lora:character_casual>"
            )
            # High score (e.g., 0.8) means both are used for similar characters
        """
        # Use pre-calculated similarity matrix if available
        if lora_a in self._similarity_cache and lora_b in self._similarity_cache[lora_a]:
            return self._similarity_cache[lora_a][lora_b]
        
        if lora_b in self._similarity_cache and lora_a in self._similarity_cache[lora_b]:
            return self._similarity_cache[lora_b][lora_a]
        

        
        # Calculate on-demand using PPMI vectors
        ppmi_a = self._get_lora_ppmi_vector(lora_a)
        ppmi_b = self._get_lora_ppmi_vector(lora_b)
        
        if not ppmi_a or not ppmi_b:
            return 0.0
        
        # Calculate dot product (shared tag associations)
        shared_tags = set(ppmi_a.keys()) & set(ppmi_b.keys())
        dot_product = sum(ppmi_a[tag] * ppmi_b[tag] for tag in shared_tags)
        
        # Calculate norms
        norm_a = self._get_lora_vector_norm(lora_a)
        norm_b = self._get_lora_vector_norm(lora_b)
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity))

    
    def get_similar_loras(
        self,
        lora: str,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find LoRAs with similar usage patterns.
        
        Use cases:
        - Find alternative/redundant LoRAs
        - Discover related LoRAs for recommendations
        - Detect LoRA groups (e.g., all character LoRAs, all style LoRAs)
        
        Args:
            lora: LoRA trigger to find similar LoRAs for
            top_k: Number of similar LoRAs to return
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of (lora_trigger, similarity_score) tuples,
            sorted by similarity (highest first)
            
        Example:
            similar = lora.get_similar_loras("<lora:character_A>", top_k=3)
            # [("<lora:character_B>", 0.85), ("<lora:character_C>", 0.72), ...]
            # These LoRAs are used in similar ways (similar tag associations)
        """
        if lora not in self.lora_matrix:
            return []
        
        similarities = []
        
        for other_lora in self.lora_matrix.keys():
            if other_lora == lora:
                continue
            
            similarity = self.calculate_lora_similarity(lora, other_lora)
            
            if similarity >= min_similarity:
                similarities.append((other_lora, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    @staticmethod
    def extract_lora_name(lora_trigger: str) -> str:
        """
        Extract clean LoRA name from trigger string.
        
        Args:
            lora_trigger: LoRA trigger (e.g., "<lora:character:1.0>")
        
        Returns:
            Clean LoRA name (e.g., "character")
            
        Example:
            extract_lora_name("<lora:Hoshino_Ichika:0.8>") → "Hoshino_Ichika"
            extract_lora_name("<lora:catcat-xl>") → "catcat-xl"
        """
        match = re.match(r"<lora:([^:>]+)", lora_trigger)
        if match:
            return match.group(1)
        return lora_trigger
    
    @classmethod
    def from_cooccurrence_matrix(cls, cooccurrence_matrix) -> "LoRAAssociation":
        """
        Create LoRAAssociation from CooccurrenceMatrix instance.
        
        The CooccurrenceMatrix contains all necessary data including
        pre-calculated similarity and conflict matrices.
        
        Args:
            cooccurrence_matrix: CooccurrenceMatrix instance
        
        Returns:
            LoRAAssociation instance
        """
        return cls(cooccurrence_matrix)
