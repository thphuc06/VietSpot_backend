from app.services.gemini_service import GeminiService
from app.services.place_supabase_service import PlaceSupabaseService
from app.services.semantic_service import SemanticSearchService
from app.services.weather_service import WeatherService
from app.services.scoring_service import ScoringService
from app.schemas.chat import ChatRequest, ChatResponse, PlaceInfo, QueryClassification
from app.core.config import settings
from typing import Optional, List, Dict, Any


class ChatbotOrchestrator:
    """
    Main orchestrator that coordinates all services to handle user queries
    """
    
    def __init__(self):
        self.gemini = GeminiService()
        self.supabase = PlaceSupabaseService()
        self.semantic = SemanticSearchService()
        self.weather = WeatherService()
        self.scoring = ScoringService()
    
    async def process_query(self, request: ChatRequest) -> ChatResponse:
        """
        Main workflow to process user query
        """
        user_prompt = request.message
        user_lat = request.user_lat
        user_lon = request.user_lon
        has_user_location = user_lat is not None and user_lon is not None
        
        print(f"📝 Original query: {user_prompt}")
        print(f"User location: {'Yes' if has_user_location else 'No'}")
        
        # Step 1: Classify query using Gemini (includes spell correction)
        classification = self.gemini.classify_query(user_prompt)
        print(f"✅ Corrected query: {classification.corrected_query}")
        print(f"Query classification: {classification.query_type}")
        print(f"Keywords: {classification.keywords}")
        print(f"Location: {classification.location_mentioned}")
        print(f"Number of places requested: {classification.number_of_places}")
        print(f"Needs semantic search: {classification.needs_semantic_search}")
        
        # Step 2: Handle general queries directly
        if classification.query_type == "general_query":
            answer = self.gemini.answer_general_query(user_prompt)
            return ChatResponse(
                answer=answer,
                places=[],
                query_type="general",
                total_places=0,
                user_location={'lat': user_lat, 'lon': user_lon} if has_user_location else None
            )
        
        # Step 3: Determine search strategy
        places = await self._search_places(classification, user_lat, user_lon)
        
        if not places:
            return ChatResponse(
                answer="Xin lỗi, tôi không tìm thấy địa điểm nào phù hợp với yêu cầu của bạn. Vui lòng thử lại với tiêu chí khác.",
                places=[],
                query_type=classification.query_type,
                total_places=0,
                user_location={'lat': user_lat, 'lon': user_lon} if has_user_location else None
            )
        
        # Step 4: Get weather information
        weather_data = None
        if has_user_location:
            weather_data = self.weather.get_weather_by_coords(user_lat, user_lon)
        elif classification.location_mentioned:
            weather_data = self.weather.get_weather_by_city(classification.location_mentioned)
        
        # Step 5: Calculate distances (if user location available)
        if has_user_location:
            for place in places:
                if 'distance_km' not in place:
                    distance = self.supabase.calculate_distance(
                        user_lat, user_lon,
                        place['latitude'], place['longitude']
                    )
                    place['distance_km'] = round(distance, 2)
        
        # Step 6: Rank and score places
        top_k = classification.number_of_places or settings.TOP_K_FINAL_RESULTS
        candidate_places = self.scoring.rank_places(
            places, 
            has_user_location=has_user_location,
            top_k=top_k * 5  # Get 3x more candidates for Gemini to select from
        )
        
        # Step 7: Let Gemini select places AND generate response
        print(f"🤖 Letting Gemini select from {len(candidate_places)} candidates and generate response...")
        selected_places, answer = self.gemini.select_places_and_generate_response(
            user_prompt=user_prompt,
            places=candidate_places,
            max_places=top_k,
            weather_data=weather_data,
            original_language=classification.original_language
        )
        print(f"✅ Gemini selected {len(selected_places)} places and generated response")
        
        # Step 7.5: Add images to selected places
        print(f"🖼️ Fetching images for {len(selected_places)} selected places...")
        selected_places = self.supabase.add_images_to_places(selected_places, max_images=5)
        
        # Step 8: Format response
        place_infos = []
        for place in selected_places:
            about_text = place.get('about', '')
            if isinstance(about_text, dict):
                about_text = str(about_text)
            
            place_info = PlaceInfo(
                place_id=place.get('id', 'unknown'),
                name=place.get('name', 'Unknown'),
                address=place.get('address'),
                latitude=place.get('latitude', 0),
                longitude=place.get('longitude', 0),
                phone=place.get('phone'),
                website=place.get('website'),
                category=place.get('category'),
                rating=place.get('rating'),
                rating_count=place.get('rating_count'),
                opening_hours=str(place.get('opening_hours', '')),
                about=about_text,
                distance_km=place.get('distance_km'),
                weather=weather_data,
                score=place.get('final_score'),
                images=place.get('images', [])
            )
            place_infos.append(place_info)
        
        return ChatResponse(
            answer=answer,
            places=place_infos,
            query_type=classification.query_type,
            total_places=len(selected_places),
            user_location={'lat': user_lat, 'lon': user_lon} if has_user_location else None
        )
    
    async def _search_places(
        self,
        classification: QueryClassification,
        user_lat: Optional[float],
        user_lon: Optional[float]
    ) -> List[Dict[str, Any]]:
        """
        Execute search strategy based on query classification
        """
        places = []
        
        # Handle nearby search with geometry
        if classification.query_type == "nearby_search" and user_lat and user_lon:
            radius_km = classification.radius_km or settings.DEFAULT_NEARBY_RADIUS_KM
            
            print(f"📍 Performing nearby search with radius: {radius_km} km")
            
            places = self.supabase.geometry_nearby_search(
                user_lat=user_lat,
                user_lon=user_lon,
                radius_km=radius_km
            )
            
            # Apply rating filter if specified
            if places and (classification.min_rating is not None or classification.max_rating is not None):
                print(f"   Applying rating filter: {classification.min_rating} - {classification.max_rating}")
                filtered_places = []
                for place in places:
                    rating = place.get('rating')
                    if rating is not None:
                        passes_min = classification.min_rating is None or rating >= classification.min_rating
                        passes_max = classification.max_rating is None or rating <= classification.max_rating
                        if passes_min and passes_max:
                            filtered_places.append(place)
                
                if filtered_places:
                    print(f"   Filtered to {len(filtered_places)} places matching rating criteria")
                    places = filtered_places
        
        # Keyword search for specific queries
        elif classification.query_type == "specific_search":
            corrected_keywords = classification.keywords
            variants = classification.keyword_variants if hasattr(classification, 'keyword_variants') else []
            print(f"🔍 Performing keyword search with keywords: {corrected_keywords}, variants: {variants}")
            print(f"   Rating filter: {classification.min_rating} - {classification.max_rating}")
            places = self.supabase.keyword_search(
                keywords=corrected_keywords,
                location=classification.location_mentioned,
                price_range=classification.price_range,
                category=classification.category,
                min_rating=classification.min_rating,
                max_rating=classification.max_rating,
                keyword_variants=variants
            )
            
            if not places and classification.keywords:
                print(f"Keyword search returned 0 results. Trying location-only filter...")
                places = self.supabase.get_all_places(limit=5000)
        
        # Fallback: get all places
        if not places:
            print("No results from any search, fetching places for semantic search")
            places = self.supabase.get_all_places(limit=5000)
        
        # Only run semantic search if query has contextual meaning that needs understanding
        if places and classification.needs_semantic_search:
            print(f"🔍 Performing semantic search on {len(places)} places (query has contextual meaning)")
            top_n = classification.number_of_places or settings.TOP_N_SEMANTIC_RESULTS
            top_n = max(top_n * 2, settings.TOP_N_SEMANTIC_RESULTS)
            
            # Use vietnamese_query for semantic search - only embed context/meaning
            # Remove location and number from query to focus on semantic meaning
            semantic_query = classification.vietnamese_query
            
            # Remove location from semantic query
            if classification.location_mentioned:
                semantic_query = semantic_query.replace(f"ở {classification.location_mentioned}", "")
                semantic_query = semantic_query.replace(f"tại {classification.location_mentioned}", "")
                semantic_query = semantic_query.replace(f"in {classification.location_mentioned}", "")
                semantic_query = semantic_query.replace(classification.location_mentioned, "")
            
            # Remove number of places from query (e.g., "12 quán" -> "quán")
            if classification.number_of_places:
                import re
                # Remove patterns like "12 ", "3 ", etc. at start or in middle
                semantic_query = re.sub(r'\b\d+\s+', '', semantic_query)
            
            # Remove common request phrases
            remove_phrases = ['cho tôi', 'tìm cho tôi', 'tìm', 'gợi ý', 'đề xuất', 'liệt kê', 'show me', 'find', 'give me']
            for phrase in remove_phrases:
                semantic_query = semantic_query.replace(phrase, '')
            
            semantic_query = ' '.join(semantic_query.split()).strip()  # Clean up whitespace
            
            print(f"Semantic search query (context only): {semantic_query}")
            places = self.semantic.hybrid_search(
                query=semantic_query,
                keyword_places=places,
                all_places=[],
                top_k=top_n
            )
            
            # Post-filter by location
            if classification.location_mentioned and len(places) > 0:
                filtered_places = []
                for place in places:
                    address = place.get('address', '').lower()
                    location_lower = classification.location_mentioned.lower()
                    if location_lower in address:
                        filtered_places.append(place)
                
                if len(filtered_places) > 0:
                    print(f"Filtered to {len(filtered_places)} places matching location in address")
                    places = filtered_places
        elif places:
            print(f"⏭️ Skipping semantic search (query has no contextual meaning, using {len(places)} keyword results directly)")
        
        return places
