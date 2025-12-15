from supabase import create_client, Client
from app.core.config import settings
from typing import List, Dict, Optional, Any
import math


class PlaceSupabaseService:
    """Service for place-related Supabase operations (chatbot functionality)"""
    
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.places_table = "places"
        self.images_table = "images"
    
    def keyword_search(
        self, 
        keywords: List[str], 
        location: Optional[str] = None,
        price_range: Optional[str] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search places by name, address, and rating only
        """
        try:
            query = self.client.table(self.places_table).select("*")
            
            if keywords and len(keywords) > 0:
                main_keyword = keywords[0]
                print(f"DEBUG: Searching with main keyword: '{main_keyword}'")
                query = query.ilike("address", f"%{main_keyword}%")
            
            if location:
                print(f"DEBUG: Adding location filter: {location}")
                query = query.ilike("address", f"%{location}%")
            
            if min_rating is not None:
                print(f"DEBUG: Adding min_rating filter: {min_rating}")
                query = query.gte("rating", min_rating)
            if max_rating is not None:
                print(f"DEBUG: Adding max_rating filter: {max_rating}")
                query = query.lte("rating", max_rating)
            
            print(f"DEBUG: Executing query without limit...")
            response = query.execute()
            print(f"DEBUG: Raw response data length: {len(response.data)}")
            final_data = response.data
            
            # Parse coordinates JSON for each result
            places = []
            for place in final_data:
                if place.get('coordinates'):
                    import json
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                places.append(place)
            
            return places
            
        except Exception as e:
            print(f"Error in keyword_search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def geometry_nearby_search(
        self,
        user_lat: float,
        user_lon: float,
        radius_km: float = 10,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search places within radius using PostGIS geometry
        """
        try:
            import json
            
            print(f"🔍 Calling nearby_places function:")
            print(f"   - user_lat: {user_lat}, user_lon: {user_lon}")
            print(f"   - radius_km: {radius_km}")
            print(f"   - limit: {limit}")
            
            response = self.client.rpc(
                'nearby_places',
                {
                    'user_lat': user_lat,
                    'user_lon': user_lon,
                    'radius_km': radius_km,
                    'place_category': None,
                    'result_limit': limit
                }
            ).execute()
            
            places = response.data
            print(f"✅ nearby_places returned {len(places)} places")
            
            filtered_places = []
            for place in places:
                if place.get('coordinates'):
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                    
                    if place['latitude'] and place['longitude']:
                        distance = self.calculate_distance(
                            user_lat, user_lon,
                            place['latitude'], place['longitude']
                        )
                        place['distance_km'] = round(distance, 2)
                        filtered_places.append(place)
                else:
                    filtered_places.append(place)
            
            return filtered_places
            
        except Exception as e:
            print(f"Error in geometry_nearby_search: {e}")
            return []
    
    def get_all_places(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """
        Get all places for semantic search
        """
        try:
            import json
            response = self.client.table(self.places_table).select("*").limit(limit).execute()
            places = []
            for place in response.data:
                if place.get('coordinates'):
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                places.append(place)
            return places
        except Exception as e:
            print(f"Error in get_all_places: {e}")
            return []
    
    def get_places_by_ids(self, place_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get places by their IDs
        """
        try:
            import json
            response = self.client.table(self.places_table).select("*").in_("id", place_ids).execute()
            places = []
            for place in response.data:
                if place.get('coordinates'):
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                places.append(place)
            return places
        except Exception as e:
            print(f"Error in get_places_by_ids: {e}")
            return []
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def filter_places_by_distance(
        self,
        places: List[Dict[str, Any]],
        user_lat: float,
        user_lon: float,
        max_distance_km: float
    ) -> List[Dict[str, Any]]:
        """
        Filter places by distance from user location
        """
        filtered = []
        for place in places:
            distance = self.calculate_distance(
                user_lat, user_lon,
                place['latitude'], place['longitude']
            )
            if distance <= max_distance_km:
                place['distance_km'] = round(distance, 2)
                filtered.append(place)
        return filtered
    
    def get_place_images(self, place_id: str, limit: int = 5) -> List[str]:
        """
        Get image URLs for a place from images table
        """
        try:
            response = self.client.table(self.images_table).select("url").eq("place_id", place_id).limit(limit).execute()
            return [img['url'] for img in response.data if img.get('url')]
        except Exception as e:
            print(f"Error getting images for place {place_id}: {e}")
            return []
    
    def add_images_to_places(self, places: List[Dict[str, Any]], max_images: int = 5) -> List[Dict[str, Any]]:
        """
        Add images to list of places by fetching from images table
        """
        for place in places:
            place_id = place.get('id')
            if place_id:
                place['images'] = self.get_place_images(place_id, max_images)
            else:
                place['images'] = []
        return places
