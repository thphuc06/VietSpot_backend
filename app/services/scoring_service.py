from typing import List, Dict, Any
from app.core.config import settings
import numpy as np


class ScoringService:
    def __init__(self):
        self.weight_semantic = settings.WEIGHT_SEMANTIC
        self.weight_distance = settings.WEIGHT_DISTANCE
        self.weight_rating = settings.WEIGHT_RATING
        self.weight_popularity = settings.WEIGHT_POPULARITY
    
    def normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 range
        """
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)
    
    def calculate_distance_score(self, distance_km: float, max_distance: float = 50) -> float:
        """
        Calculate distance score (closer = higher score)
        Score decreases exponentially with distance
        """
        if distance_km <= 0:
            return 1.0
        if distance_km >= max_distance:
            return 0.0
        
        # Exponential decay: score = e^(-distance/scale)
        scale = max_distance / 3
        score = np.exp(-distance_km / scale)
        return score
    
    def calculate_rating_score(self, rating: float) -> float:
        """
        Normalize rating to 0-1 scale (assuming ratings are 0-5)
        """
        if rating is None or rating <= 0:
            return 0.5  # Default score for no rating
        return min(rating / 5.0, 1.0)
    
    def calculate_popularity_score(self, place: Dict[str, Any]) -> float:
        """
        Calculate popularity based on various factors
        """
        num_reviews = place.get('num_reviews', 0)
        num_checkins = place.get('num_checkins', 0)
        
        # Simple popularity score
        popularity = (num_reviews * 0.6 + num_checkins * 0.4) / 100
        return min(popularity, 1.0)
    
    def calculate_combined_score(
        self,
        place: Dict[str, Any],
        has_user_location: bool = False
    ) -> float:
        """
        Calculate combined score for a place based on multiple factors
        """
        scores = {}
        
        # Semantic score (from semantic search)
        semantic_score = place.get('semantic_score', 0.5)
        scores['semantic'] = semantic_score * self.weight_semantic
        
        # Distance score (only if user location is provided)
        if has_user_location and 'distance_km' in place:
            distance_score = self.calculate_distance_score(place['distance_km'])
            scores['distance'] = distance_score * self.weight_distance
        else:
            scores['distance'] = 0.5 * self.weight_distance  # Neutral score
        
        # Rating score
        rating = place.get('rating', 0)
        rating_score = self.calculate_rating_score(rating)
        scores['rating'] = rating_score * self.weight_rating
        
        # Popularity score
        popularity_score = self.calculate_popularity_score(place)
        scores['popularity'] = popularity_score * self.weight_popularity
        
        # Total score
        total_score = sum(scores.values())
        
        # Store individual scores for debugging
        place['score_breakdown'] = scores
        
        return total_score
    
    def rank_places(
        self,
        places: List[Dict[str, Any]],
        has_user_location: bool = False,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Calculate scores for all places and rank them
        Returns top K places
        """
        if not places:
            return []
        
        # Calculate scores
        for place in places:
            score = self.calculate_combined_score(place, has_user_location)
            place['final_score'] = round(score, 4)
        
        # Sort by score (highest first)
        ranked_places = sorted(places, key=lambda x: x['final_score'], reverse=True)
        
        # Return top K
        return ranked_places[:top_k]
    
    def adjust_weights(
        self,
        semantic: float = None,
        distance: float = None,
        rating: float = None,
        popularity: float = None
    ):
        """
        Dynamically adjust weights for different scenarios
        """
        if semantic is not None:
            self.weight_semantic = semantic
        if distance is not None:
            self.weight_distance = distance
        if rating is not None:
            self.weight_rating = rating
        if popularity is not None:
            self.weight_popularity = popularity
        
        # Normalize weights to sum to 1.0
        total = self.weight_semantic + self.weight_distance + self.weight_rating + self.weight_popularity
        if total > 0:
            self.weight_semantic /= total
            self.weight_distance /= total
            self.weight_rating /= total
            self.weight_popularity /= total
