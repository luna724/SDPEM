"""
Similarity Matrix for Tag Redundancy Detection

Uses PPMI (Positive Pointwise Mutual Information) vectors and cosine similarity
to detect **distributional/contextual similarity** between tags.

## Purpose: Avoid Meaningless Prompt Redundancy

### 1. Redundancy Elimination
When user selects "bikini", if AI suggests "swimsuit" as a candidate,
calculate_similarity("bikini", "swimsuit") will be high (e.g., 0.8)
because both appear in similar contexts (beach, pool, water).
→ Remove "swimsuit" from candidates to avoid redundancy.

### 2. Diversity Assurance
When building candidate lists, select tags with low mutual similarity
to create varied, rich prompt compositions.

## How It Works

**Distributional Similarity**: Tags used in similar contexts are similar.
- "bikini" appears with: [beach, pool, water, solo, 1girl, ...]
- "swimsuit" appears with: [beach, pool, water, solo, 1girl, ...]
→ Similar co-occurrence patterns → High similarity score

This is NOT "tags that appear together" (co-occurrence).
This IS "tags that appear in similar contexts" (distributional similarity).

## Example Use Cases

```python
# Check if two tags are redundant
if sim.calculate_similarity("bikini", "swimsuit") > 0.7:
    print("Too similar! Skip suggesting swimsuit.")

# Get diverse tag candidates
candidates = ["swimsuit", "beach", "summer", "bikini", "water"]
diverse_tags = sim.filter_diverse_tags(candidates, max_similarity=0.5)
# Result: ["swimsuit", "beach", "summer"] (bikini removed as redundant)
```
"""

import math
from typing import Dict, List, Set, Tuple


class SimilarityMatrix:
    """
    Calculates distributional similarity between tags using PPMI-based cosine similarity.
    
    **Key Idea**: Tags that co-occur with similar sets of other tags are semantically similar.
    
    - PPMI = max(0, PMI) - focuses on positive associations only
    - Cosine Similarity = measures how similar two tag contexts are
    """
    
    def __init__(self, matrix_data: dict[str, dict[str, float]]):
        """
        Initialize with PMI matrix data.
        
        Args:
            matrix_data: PMI matrix from CooccurrenceMatrix (tag -> other_tag -> pmi_score)
        """
        self.matrix_data = matrix_data
        self._ppmi_cache: Dict[str, Dict[str, float]] = {}
        self._norm_cache: Dict[str, float] = {}
    
    def _get_ppmi_vector(self, tag: str) -> Dict[str, float]:
        """
        Get PPMI (Positive PMI) context vector for a tag.
        
        The vector represents "which other tags does this tag co-occur with?"
        PPMI(x, y) = max(0, PMI(x, y))
        
        Returns:
            Dictionary mapping context tags to PPMI scores
        """
        if tag in self._ppmi_cache:
            return self._ppmi_cache[tag]
        
        if tag not in self.matrix_data:
            self._ppmi_cache[tag] = {}
            return {}
        
        # Convert PMI to PPMI (keep only positive co-occurrence patterns)
        ppmi_vector = {
            other_tag: max(0.0, pmi_score)
            for other_tag, pmi_score in self.matrix_data[tag].items()
        }
        
        self._ppmi_cache[tag] = ppmi_vector
        return ppmi_vector
    
    def _get_vector_norm(self, tag: str) -> float:
        """
        Calculate L2 norm (magnitude) of PPMI context vector.
        ||v|| = sqrt(sum(v_i^2))
        """
        if tag in self._norm_cache:
            return self._norm_cache[tag]
        
        ppmi_vector = self._get_ppmi_vector(tag)
        
        if not ppmi_vector:
            self._norm_cache[tag] = 0.0
            return 0.0
        
        norm = math.sqrt(sum(score ** 2 for score in ppmi_vector.values()))
        self._norm_cache[tag] = norm
        return norm
    
    def calculate_similarity(self, tag_a: str, tag_b: str) -> float:
        """
        Calculate distributional similarity between two tags.
        
        **High similarity means**: Both tags appear in similar contexts (redundant).
        **Low similarity means**: Tags appear in different contexts (diverse).
        
        Examples:
        - calculate_similarity("bikini", "swimsuit") → ~0.8 (redundant)
        - calculate_similarity("bikini", "sword") → ~0.1 (diverse)
        
        Method: Cosine similarity of PPMI context vectors
        cos(A, B) = (A · B) / (||A|| * ||B||)
        
        Args:
            tag_a: First tag
            tag_b: Second tag
        
        Returns:
            Similarity score in range [0, 1]
            - 1.0 = extremely similar contexts (highly redundant)
            - 0.0 = completely different contexts (maximally diverse)
        """
        # Get PPMI context vectors
        ppmi_a = self._get_ppmi_vector(tag_a)
        ppmi_b = self._get_ppmi_vector(tag_b)
        
        # Handle edge cases
        if not ppmi_a or not ppmi_b:
            return 0.0
        
        # Calculate dot product (shared context strength)
        shared_context = set(ppmi_a.keys()) & set(ppmi_b.keys())
        dot_product = sum(ppmi_a[tag] * ppmi_b[tag] for tag in shared_context)
        
        # Calculate norms
        norm_a = self._get_vector_norm(tag_a)
        norm_b = self._get_vector_norm(tag_b)
        
        # Avoid division by zero
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        
        # Cosine similarity
        similarity = dot_product / (norm_a * norm_b)
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, similarity))
    
    def get_similar_tags(self, tag: str, top_k: int = 10, min_similarity: float = 0.3) -> List[Tuple[str, float]]:
        """
        Find most similar (potentially redundant) tags.
        
        Use this to:
        - Identify redundant tags to avoid suggesting
        - Find alternative tags with similar meanings
        
        Args:
            tag: Tag to find similar tags for
            top_k: Number of similar tags to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
        
        Returns:
            List of (tag, similarity_score) tuples, sorted by similarity (highest first)
        """
        if tag not in self.matrix_data:
            return []
        
        similarities = []
        
        for other_tag in self.matrix_data.keys():
            if other_tag == tag:
                continue
            
            similarity = self.calculate_similarity(tag, other_tag)
            
            if similarity >= min_similarity:
                similarities.append((other_tag, similarity))
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def is_redundant(self, tag_a: str, tag_b: str, threshold: float = 0.6) -> bool:
        """
        Check if two tags are redundant (too similar).
        
        Recommended thresholds:
        - 0.8+: Extremely redundant (e.g., "bikini" vs "swimsuit")
        - 0.6-0.8: Moderately redundant
        - 0.4-0.6: Somewhat related but acceptable
        - <0.4: Diverse enough
        
        Args:
            tag_a: First tag
            tag_b: Second tag
            threshold: Redundancy threshold (default 0.6)
        
        Returns:
            True if similarity >= threshold (tags are redundant)
        """
        return self.calculate_similarity(tag_a, tag_b) >= threshold
    
    def filter_redundant_tags(
        self, 
        tags: List[str], 
        max_similarity: float = 0.6
    ) -> List[str]:
        """
        Remove redundant tags from a list, keeping only diverse tags.
        
        Algorithm:
        1. Start with the first tag
        2. For each subsequent tag, check if it's too similar to any kept tag
        3. If not redundant, keep it; otherwise skip
        
        Args:
            tags: List of candidate tags
            max_similarity: Maximum allowed similarity between kept tags
        
        Returns:
            Filtered list with redundant tags removed
            
        Example:
            candidates = ["bikini", "swimsuit", "beach", "pool"]
            diverse = sim.filter_redundant_tags(candidates, max_similarity=0.6)
            # Result: ["bikini", "beach"] (removed "swimsuit" and "pool" as redundant)
        """
        if not tags:
            return []
        
        kept_tags = [tags[0]]  # Always keep the first tag
        
        for candidate in tags[1:]:
            # Check if candidate is too similar to any already-kept tag
            is_redundant = any(
                self.calculate_similarity(candidate, kept) >= max_similarity
                for kept in kept_tags
            )
            
            if not is_redundant:
                kept_tags.append(candidate)
        
        return kept_tags
    
    def get_diverse_candidates(
        self,
        base_tags: Set[str],
        candidate_tags: List[str],
        max_count: int = 10,
        min_diversity: float = 0.4
    ) -> List[str]:
        """
        Select diverse candidates that don't overlap with base tags.
        
        Use this when building prompt suggestions:
        - base_tags: Tags already in the prompt
        - candidate_tags: Potential tags to add
        - Returns: Diverse, non-redundant candidates
        
        Args:
            base_tags: Tags already selected
            candidate_tags: Pool of potential tags to add
            max_count: Maximum number of candidates to return
            min_diversity: Minimum required diversity (1.0 - max_similarity)
        
        Returns:
            List of diverse candidate tags
            
        Example:
            current_prompt = {"1girl", "bikini", "beach"}
            candidates = ["swimsuit", "water", "sky", "clouds", "ocean"]
            suggestions = sim.get_diverse_candidates(
                current_prompt, candidates, max_count=3, min_diversity=0.5
            )
            # Returns tags that are diverse and don't redundantly overlap with "bikini"/"beach"
        """
        max_similarity = 1.0 - min_diversity
        diverse_candidates = []
        
        for candidate in candidate_tags:
            # Skip if candidate is too similar to any base tag
            too_similar_to_base = any(
                self.calculate_similarity(candidate, base) >= max_similarity
                for base in base_tags
            )
            
            if too_similar_to_base:
                continue
            
            # Skip if candidate is too similar to already-selected diverse candidates
            too_similar_to_selected = any(
                self.calculate_similarity(candidate, selected) >= max_similarity
                for selected in diverse_candidates
            )
            
            if too_similar_to_selected:
                continue
            
            diverse_candidates.append(candidate)
            
            if len(diverse_candidates) >= max_count:
                break
        
        return diverse_candidates
    
    @classmethod
    def from_cooccurrence_matrix(cls, cooccurrence_matrix) -> "SimilarityMatrix":
        """
        Create SimilarityMatrix from CooccurrenceMatrix instance.
        
        Args:
            cooccurrence_matrix: CooccurrenceMatrix instance
        
        Returns:
            SimilarityMatrix instance
        """
        return cls(cooccurrence_matrix.matrix)