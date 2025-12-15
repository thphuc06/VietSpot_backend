from sentence_transformers import SentenceTransformer, util
from app.core.config import settings
from typing import List, Dict, Any
import numpy as np


class SemanticSearchService:
    def __init__(self):
        # Load multilingual model that supports Vietnamese
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.places_embeddings = {}
        self.places_data = []
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Create embedding for user query
        """
        try:
            embedding = self.model.encode(query, convert_to_tensor=False)
            return embedding
        except Exception as e:
            print(f"Error in embed_query: {e}")
            return np.array([])
    
    def embed_places(self, places: List[Dict[str, Any]]) -> None:
        """
        Create embeddings for all places and cache them
        OPTIMIZATION: Use pre-computed embeddings from database 'embed' column if available
        """
        try:
            if not places or len(places) == 0:
                return
                
            self.places_data = places
            
            # Check if places have pre-computed embeddings
            has_precomputed = all(place.get('embed') is not None for place in places)
            
            if has_precomputed:
                # FAST PATH: Use pre-computed embeddings from database
                print(f"Using pre-computed embeddings for {len(places)} places")
                for place in places:
                    place_id = place.get('id')
                    embed = place.get('embed')
                    if place_id and embed:
                        try:
                            if isinstance(embed, str):
                                import json
                                embed = np.array(json.loads(embed), dtype=np.float32)
                            elif isinstance(embed, list):
                                embed = np.array(embed, dtype=np.float32)
                            elif isinstance(embed, np.ndarray):
                                embed = embed.astype(np.float32)
                            else:
                                continue
                            
                            self.places_embeddings[place_id] = embed
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"Error parsing embedding for place {place_id}: {e}")
                            continue
                return
            
            # SLOW PATH: Generate embeddings on-the-fly
            print(f"Generating embeddings for {len(places)} places...")
            texts = []
            valid_places = []
            
            for place in places:
                about_text = place.get('about', '')
                if isinstance(about_text, dict):
                    description = about_text.get('description', '')
                    about_text = description[:200] if description else str(about_text)[:200]
                elif isinstance(about_text, str):
                    about_text = about_text[:200]
                else:
                    about_text = ''
                
                name = place.get('name', '')
                category = place.get('category', '')
                
                if name or about_text or category:
                    text = f"{name} {about_text} {category}".strip()[:500]
                    texts.append(text)
                    valid_places.append(place)
            
            if len(texts) > 0:
                embeddings = self.model.encode(
                    texts, 
                    convert_to_tensor=False, 
                    show_progress_bar=False,
                    batch_size=32,
                    normalize_embeddings=True
                )
                
                if not isinstance(embeddings, np.ndarray):
                    embeddings = np.array(embeddings)
                
                min_len = min(len(embeddings), len(valid_places))
                
                for idx in range(min_len):
                    try:
                        place = valid_places[idx]
                        place_id = place.get('id')
                        if place_id:
                            self.places_embeddings[place_id] = embeddings[idx]
                    except (IndexError, KeyError) as e:
                        print(f"Error storing embedding at index {idx}: {e}")
                        continue
                
        except Exception as e:
            import traceback
            print(f"Error in embed_places: {e}")
            print(traceback.format_exc())
    
    def semantic_search(
        self, 
        query_embedding: np.ndarray, 
        places: List[Dict[str, Any]], 
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search and return top K places with similarity scores
        """
        try:
            if len(query_embedding) == 0 or len(places) == 0:
                return []
            
            # Ensure places are embedded
            if not self.places_embeddings or len(self.places_embeddings) != len(places):
                self.embed_places(places)
            
            # Calculate cosine similarity
            similarities = []
            for place in places:
                place_id = place.get('id')
                if place_id in self.places_embeddings:
                    place_embedding = self.places_embeddings[place_id]
                    similarity = util.cos_sim(query_embedding, place_embedding).item()
                    similarities.append({
                        'place': place,
                        'semantic_score': similarity
                    })
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['semantic_score'], reverse=True)
            
            # Get top K results
            top_results = similarities[:top_k]
            
            # Add semantic score to place data
            result_places = []
            for item in top_results:
                place = item['place'].copy()
                place['semantic_score'] = round(item['semantic_score'], 4)
                result_places.append(place)
            
            return result_places
            
        except Exception as e:
            print(f"Error in semantic_search: {e}")
            return places[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        keyword_places: List[Dict[str, Any]],
        all_places: List[Dict[str, Any]],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Combine keyword search results with semantic search
        """
        try:
            # Embed the query
            query_embedding = self.embed_query(query)
            
            # Determine which places to search
            search_pool = keyword_places if keyword_places else all_places
            
            # Perform semantic search
            results = self.semantic_search(query_embedding, search_pool, top_k)
            
            return results
            
        except Exception as e:
            print(f"Error in hybrid_search: {e}")
            return keyword_places[:top_k] if keyword_places else all_places[:top_k]
