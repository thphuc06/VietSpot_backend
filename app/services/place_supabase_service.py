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
        max_rating: Optional[float] = None,
        keyword_variants: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search places by address for location terms, and by name for place names.
        Uses OR logic: match ANY keyword variant
        Also searches in category field for activity-based queries (e.g., "đi tắm" -> "Biển & Bãi Biển")
        """
        try:
            query = self.client.table(self.places_table).select("*")
            
            # Known city/district names (search only in address)
            city_district_keywords = [
                'hồ chí minh', 'ho chi minh', 'hcm', 'sài gòn', 'saigon',
                'hà nội', 'ha noi', 'hanoi',
                'đà nẵng', 'da nang', 'danang',
                'vũng tàu', 'vung tau', 'nha trang', 'phú quốc', 'phu quoc',
                'đà lạt', 'da lat', 'hội an', 'hoi an', 'huế', 'hue',
                'quận', 'quan', 'district', 'phường', 'phuong', 'ward',
                'bình thạnh', 'binh thanh', 'thủ đức', 'thu duc',
                'tân bình', 'tan binh', 'gò vấp', 'go vap',
            ]
            
            # Category keywords mapping for activity-based searches
            category_keywords = {
                'bãi biển': 'Biển & Bãi Biển', 'bai bien': 'Biển & Bãi Biển',
                'beach': 'Biển & Bãi Biển', 'bãi tắm': 'Biển & Bãi Biển', 'bai tam': 'Biển & Bãi Biển',
                'biển': 'Biển & Bãi Biển', 'bien': 'Biển & Bãi Biển',
                'bảo tàng': 'Bảo Tàng & Triển Lãm', 'bao tang': 'Bảo Tàng & Triển Lãm',
                'museum': 'Bảo Tàng & Triển Lãm', 'triển lãm': 'Bảo Tàng & Triển Lãm',
                'cà phê': 'Quán Cà Phê', 'ca phe': 'Quán Cà Phê', 'cafe': 'Quán Cà Phê', 'coffee': 'Quán Cà Phê',
                'nhà hàng': 'Nhà Hàng', 'nha hang': 'Nhà Hàng', 'restaurant': 'Nhà Hàng',
                'công viên': 'Công Viên', 'cong vien': 'Công Viên', 'park': 'Công Viên',
                'di tích': 'Di Tích Lịch Sử', 'di tich': 'Di Tích Lịch Sử', 'lịch sử': 'Di Tích Lịch Sử',
            }
            
            # Combine all search terms
            all_search_terms = []
            if keyword_variants and len(keyword_variants) > 0:
                all_search_terms.extend(keyword_variants)
            if keywords:
                all_search_terms.extend(keywords)
            if location:
                all_search_terms.append(location)
            
            # Remove duplicates
            all_search_terms = list(set([term for term in all_search_terms if term and term.strip()]))
            
            # Detect category from search terms
            detected_categories = set()
            for term in all_search_terms:
                term_lower = term.lower()
                if term_lower in category_keywords:
                    detected_categories.add(category_keywords[term_lower])
            
            # Separate location terms and other terms
            location_filters = []
            category_filters = []
            name_filters = []
            
            for term in all_search_terms:
                term_lower = term.lower()
                is_location_term = any(loc in term_lower for loc in city_district_keywords)
                is_category_term = term_lower in category_keywords
                
                if is_location_term:
                    location_filters.append(f"address.ilike.%{term}%")
                elif is_category_term:
                    db_category = category_keywords[term_lower]
                    # Use simpler category match (avoid special characters issue)
                    category_filters.append(f"category.ilike.%{db_category}%")
                else:
                    name_filters.append(f"name.ilike.%{term}%")
                    name_filters.append(f"address.ilike.%{term}%")
            
            print(f"DEBUG: location_filters: {location_filters}")
            print(f"DEBUG: category_filters: {category_filters}")
            print(f"DEBUG: name_filters: {name_filters[:4]}...")
            
            # Strategy: Query by location in DB, then filter by category in Python
            # This avoids issues with special characters in category names
            if location_filters:
                location_or = ",".join(location_filters)
                print(f"DEBUG: Filtering by location: {location_or}")
                query = query.or_(location_or)
            
            if name_filters and not location_filters:
                # Only use name filters if no location specified
                filter_string = ",".join(name_filters)
                print(f"DEBUG: Using name filters: {len(name_filters)} filters")
                query = query.or_(filter_string)
            
            if min_rating is not None:
                print(f"DEBUG: Adding min_rating filter: {min_rating}")
                query = query.gte("rating", min_rating)
            if max_rating is not None:
                print(f"DEBUG: Adding max_rating filter: {max_rating}")
                query = query.lte("rating", max_rating)
            
            print(f"DEBUG: Executing query...")
            response = query.execute()
            print(f"DEBUG: Raw response data length: {len(response.data)}")
            
            # Parse coordinates and calculate match score
            places = []
            for place in response.data:
                if place.get('coordinates'):
                    import json
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                
                # Calculate match score
                name = (place.get('name') or '').lower()
                address = (place.get('address') or '').lower()
                place_category = (place.get('category') or '').lower()
                match_count = 0
                category_matched = False
                
                for term in all_search_terms:
                    term_lower = term.lower()
                    if term_lower in name:
                        match_count += 2  # Name match worth more
                    if term_lower in address:
                        match_count += 1
                
                # Check category match (filter in Python instead of SQL)
                for detected_cat in detected_categories:
                    if detected_cat.lower() in place_category:
                        match_count += 10  # Category match is very important
                        category_matched = True
                        
                place['keyword_match_score'] = match_count
                place['category_matched'] = category_matched
                
                places.append(place)
            
            # If we have category filters, prioritize places that match category
            if detected_categories:
                # Filter to only include places that match category
                category_matched_places = [p for p in places if p.get('category_matched')]
                if category_matched_places:
                    print(f"DEBUG: Found {len(category_matched_places)} places matching category")
                    places = category_matched_places
                else:
                    print(f"DEBUG: No places matched category, returning all {len(places)} places")
            
            # Sort by match score
            places.sort(key=lambda x: x.get('keyword_match_score', 0), reverse=True)
            
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
