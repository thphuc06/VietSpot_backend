from typing import List, Dict, Any, Optional
from app.services.place_supabase_service import PlaceSupabaseService
from app.services.gemini_service import GeminiService
from app.services.scoring_service import ScoringService
from app.services.weather_service import WeatherService
from app.schemas.itinerary import ItineraryRequest, ItineraryResponse, DayItinerary, ActivityDetail
import json
import math


class ItineraryService:
    """Service for generating travel itineraries with smart place selection"""
    
    # Category mapping from activity type to database categories
    # Database has: "Biển & Bãi Biển" (924), "Bảo Tàng & Triển Lãm" (76)
    CATEGORY_MAPPING = {
        'beach': ['Biển & Bãi Biển'],
        'museum': ['Bảo Tàng & Triển Lãm'],
        'attractions': ['Biển & Bãi Biển', 'Bảo Tàng & Triển Lãm'],  # Both
    }
    
    # Time slots for each activity type (hour in 24h format)
    TIME_SLOTS = {
        'morning_activity': (8, 11),
        'lunch_break': (11, 13),
        'afternoon_activity': (14, 17),
        'evening_activity': (17, 20),
    }
    
    def __init__(self):
        self.supabase = PlaceSupabaseService()
        self.gemini = GeminiService()
        self.scoring = ScoringService()
        self.weather = WeatherService()
    
    def generate_itinerary(self, request: ItineraryRequest) -> ItineraryResponse:
        """Generate complete itinerary by querying city places and letting Gemini reason"""
        print(f"\n🗓️ Generating {request.num_days}-day itinerary for {request.destination}")
        
        # 1. Get weather data for destination
        weather_data = self._get_weather_for_destination(request.destination)
        weather_summary = self._format_weather_summary(weather_data)
        
        # 2. Query ALL places for this city from database
        all_places = self._query_places_by_city(request.destination)
        print(f"📍 Found {len(all_places)} places in {request.destination}")
        
        if not all_places:
            print(f"⚠️ No places found for {request.destination}")
            return self._create_empty_itinerary(request)
        
        # 3. Score places if we have user location
        if request.user_lat and request.user_lon:
            all_places = self.scoring.rank_places(all_places, has_user_location=True)
        
        # 4. Let Gemini create itinerary from all available places
        itinerary_data = self._gemini_create_itinerary(
            request, 
            all_places,
            weather_data,
            weather_summary
        )
        
        return itinerary_data
    
    def _query_places_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Query all places for a specific city from database"""
        print(f"🔍 Querying places for city: {city}")
        
        try:
            # Search by city name in address - use correct column names from database
            response = self.supabase.client.table("places").select(
                "id, name, address, category, rating, rating_count, coordinates, opening_hours, about"
            ).ilike("address", f"%{city}%").limit(100).execute()
            
            places = response.data or []
            
            # Extract lat/lon from coordinates jsonb
            for place in places:
                coords = place.get('coordinates') or {}
                place['latitude'] = coords.get('lat')
                place['longitude'] = coords.get('lon')
            
            # Also try variations of city name
            city_variants = self._get_city_variants(city)
            for variant in city_variants:
                if variant.lower() != city.lower():
                    response2 = self.supabase.client.table("places").select(
                        "id, name, address, category, rating, rating_count, coordinates, opening_hours, about"
                    ).ilike("address", f"%{variant}%").limit(50).execute()
                    
                    # Add unique places with lat/lon extracted
                    existing_ids = {p['id'] for p in places}
                    for place in response2.data or []:
                        if place['id'] not in existing_ids:
                            coords = place.get('coordinates') or {}
                            place['latitude'] = coords.get('lat')
                            place['longitude'] = coords.get('lon')
                            places.append(place)
            
            print(f"   Found {len(places)} total places")
            return places
            
        except Exception as e:
            print(f"❌ Error querying places: {e}")
            return []
    
    def _get_city_variants(self, city: str) -> List[str]:
        """Get variants of city name for better matching"""
        variants = [city]
        
        # Common Vietnamese city name variants
        city_map = {
            "vũng tàu": ["vũng tàu", "vung tau", "bà rịa"],
            "hồ chí minh": ["hồ chí minh", "ho chi minh", "sài gòn", "saigon", "hcm"],
            "hà nội": ["hà nội", "ha noi", "hanoi"],
            "đà nẵng": ["đà nẵng", "da nang", "danang"],
            "nha trang": ["nha trang", "khánh hòa"],
            "đà lạt": ["đà lạt", "da lat", "dalat", "lâm đồng"],
            "phú quốc": ["phú quốc", "phu quoc", "kiên giang"],
            "huế": ["huế", "hue", "thừa thiên huế"],
            "hội an": ["hội an", "hoi an", "quảng nam"],
        }
        
        city_lower = city.lower()
        for key, values in city_map.items():
            if city_lower in values or any(v in city_lower for v in values):
                variants.extend(values)
                break
        
        return list(set(variants))
    
    def _gemini_create_itinerary(
        self,
        request: ItineraryRequest,
        all_places: List[Dict[str, Any]],
        weather_data: Optional[Dict[str, Any]],
        weather_summary: str
    ) -> ItineraryResponse:
        """Let Gemini reason about all places and create an optimal itinerary"""
        
        # Format places for Gemini - include key info only to save tokens
        places_text = self._format_places_for_gemini(all_places)
        
        weather_context = ""
        if weather_data:
            weather_context = f"""
THÔNG TIN THỜI TIẾT:
{weather_summary}
- Nếu trời mưa/nóng: ưu tiên địa điểm trong nhà
- Nếu trời đẹp: có thể tham quan ngoài trời
"""
        
        prompt = f"""Bạn là chuyên gia lập lịch trình du lịch Việt Nam.

DANH SÁCH ĐỊA ĐIỂM TẠI {request.destination.upper()}:
{places_text}

{weather_context}

YÊU CẦU:
- Tạo lịch trình {request.num_days} ngày tại {request.destination}
- Sở thích: {', '.join(request.preferences) if request.preferences else 'Khám phá tổng quát'}
- Giờ bắt đầu: {request.start_time}, kết thúc: {request.end_time}

HƯỚNG DẪN:
1. CHỌN địa điểm từ danh sách trên (dùng đúng tên và thông tin)
2. Mỗi ngày 4-6 hoạt động, mỗi ngày có CHỦ ĐỀ KHÁC NHAU
3. Sắp xếp địa điểm gần nhau trong cùng ngày
4. Đa dạng loại hình: bãi biển, bảo tàng, di tích, tham quan
5. Không lặp lại địa điểm giữa các ngày
6. LẤY ĐÚNG TỌA ĐỘ (latitude, longitude) từ danh sách nếu có

TRẢ VỀ JSON:
{{
  "destination": "{request.destination}",
  "num_days": {request.num_days},
  "itinerary": [
    {{
      "day": 1,
      "theme": "Chủ đề ngày 1",
      "activities": [
        {{
          "time": "08:00",
          "duration_minutes": 90,
          "activity_type": "visit",
          "place_name": "Tên địa điểm từ danh sách",
          "address": "Địa chỉ đầy đủ",
          "latitude": 10.123456,
          "longitude": 107.123456,
          "rating": 4.5,
          "category": "Category",
          "description": "Mô tả hoạt động"
        }}
      ],
      "total_activities": 5
    }}
  ],
  "summary": "Tóm tắt lịch trình",
  "total_places": 15,
  "tips": ["Tip 1", "Tip 2"]
}}

CHỈ TRẢ VỀ JSON, KHÔNG THÊM TEXT."""

        try:
            response_text = self.gemini.generate_with_json(prompt)
            print(f"📝 Gemini response length: {len(response_text)} chars")
            
            # Try to parse JSON with multiple methods
            itinerary_dict = self._parse_json_response(response_text)
            
            if itinerary_dict:
                return ItineraryResponse(**itinerary_dict)
            else:
                raise ValueError("Could not parse JSON response")
                
        except Exception as e:
            print(f"❌ Error in Gemini itinerary: {e}")
            print(f"   Response preview: {response_text[:300] if 'response_text' in dir() else 'N/A'}...")
            return self._create_fallback_from_places(request, all_places, weather_data)
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Try multiple methods to parse JSON from Gemini response"""
        import re
        
        # Method 1: Direct parse
        try:
            return json.loads(text)
        except:
            pass
        
        # Method 2: Extract from markdown code block
        try:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
        
        # Method 3: Find JSON object in text
        try:
            start = text.find('{')
            if start != -1:
                brace_count = 0
                for i in range(start, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = text[start:i+1]
                            return json.loads(json_str)
        except:
            pass
        
        # Method 4: Try to fix common JSON issues
        try:
            # Remove trailing commas
            fixed = re.sub(r',\s*}', '}', text)
            fixed = re.sub(r',\s*]', ']', fixed)
            return json.loads(fixed)
        except:
            pass
        
        return None
    
    def _format_places_for_gemini(self, places: List[Dict[str, Any]]) -> str:
        """Format places list for Gemini prompt - include coordinates"""
        lines = []
        for i, place in enumerate(places[:80], 1):  # Limit to 80 places
            name = place.get('name', 'N/A')
            category = place.get('category', '')
            rating = place.get('rating', 'N/A')
            address = place.get('address', '')[:50] if place.get('address') else ''
            lat = place.get('latitude', '')
            lon = place.get('longitude', '')
            
            # Include coordinates if available
            coord_str = f"({lat},{lon})" if lat and lon else ""
            lines.append(f"{i}. {name} | {category} | ⭐{rating} | {address} {coord_str}")
        
        return "\n".join(lines)
    
    def _create_empty_itinerary(self, request: ItineraryRequest) -> ItineraryResponse:
        """Create empty itinerary when no places found"""
        return ItineraryResponse(
            destination=request.destination,
            num_days=request.num_days,
            itinerary=[],
            summary=f"Không tìm thấy địa điểm nào tại {request.destination}",
            total_places=0,
            tips=["Vui lòng thử lại với tên thành phố khác"]
        )
    
    def _create_fallback_from_places(
        self, 
        request: ItineraryRequest, 
        places: List[Dict[str, Any]],
        weather_data: Optional[Dict[str, Any]]
    ) -> ItineraryResponse:
        """Create simple fallback itinerary from available places"""
        days = []
        places_per_day = min(5, len(places) // request.num_days) if places else 0
        used_places = set()
        
        for day_num in range(1, request.num_days + 1):
            activities = []
            start_idx = (day_num - 1) * places_per_day
            day_places = [p for p in places[start_idx:start_idx + places_per_day] if p['id'] not in used_places]
            
            times = ["08:30", "10:30", "14:00", "16:00", "18:00"]
            
            for i, place in enumerate(day_places[:5]):
                used_places.add(place['id'])
                activities.append(ActivityDetail(
                    time=times[i],
                    duration_minutes=90,
                    activity_type="visit",
                    place_id=str(place.get('id', '')),
                    place_name=place.get('name', 'Unknown'),
                    address=place.get('address'),
                    latitude=place.get('latitude'),
                    longitude=place.get('longitude'),
                    rating=place.get('rating'),
                    category=place.get('category'),
                    description=f"Tham quan {place.get('name')}"
                ))
            
            days.append(DayItinerary(
                day=day_num,
                theme=f"Khám phá {request.destination} - Ngày {day_num}",
                activities=activities,
                total_activities=len(activities)
            ))
        
        tips = ["Mang theo nước", "Đi giày thoải mái"]
        if weather_data:
            advice = self.weather.get_weather_advice(weather_data)
            if advice:
                tips.insert(0, advice)
        
        return ItineraryResponse(
            destination=request.destination,
            num_days=request.num_days,
            itinerary=days,
            summary=f"Lịch trình {request.num_days} ngày tại {request.destination}",
            total_places=sum(len(d.activities) for d in days),
            tips=tips
        )
    
    def _get_weather_for_destination(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get weather data for the destination"""
        print(f"🌤️ Fetching weather for {destination}...")
        weather = self.weather.get_weather_by_city(destination)
        if weather:
            print(f"   Temperature: {weather.get('temp')}°C, {weather.get('description')}")
        return weather
    
    def _format_weather_summary(self, weather_data: Optional[Dict[str, Any]]) -> str:
        """Format weather data into a summary string"""
        if not weather_data:
            return "Không có thông tin thời tiết"
        
        temp = weather_data.get('temp', 'N/A')
        feels_like = weather_data.get('feels_like', 'N/A')
        description = weather_data.get('description', 'N/A')
        humidity = weather_data.get('humidity', 'N/A')
        
        advice = self.weather.get_weather_advice(weather_data)
        
        return f"""Nhiệt độ: {temp}°C (cảm giác như {feels_like}°C)
Thời tiết: {description}
Độ ẩm: {humidity}%
Lời khuyên: {advice}"""
    
    def _fetch_and_score_places(
        self, 
        location: str,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch places from database, score and rank them"""
        print(f"📍 Fetching and scoring places in {location}...")
        
        has_user_location = user_lat is not None and user_lon is not None
        places_by_category = {}
        
        for activity_type, categories in self.CATEGORY_MAPPING.items():
            print(f"   Searching {activity_type}...")
            
            # Search by category and location
            places = self._search_by_category_and_location(categories, location)
            
            if not places:
                # Fallback to keyword search
                places = self.supabase.keyword_search(
                    keywords=categories[:2],
                    keyword_variants=categories,
                    location=location,
                    min_rating=3.5
                )
            
            if places:
                # Calculate distance if user location available
                if has_user_location:
                    for place in places:
                        if place.get('latitude') and place.get('longitude'):
                            distance = self.supabase.calculate_distance(
                                user_lat, user_lon,
                                place['latitude'], place['longitude']
                            )
                            place['distance_km'] = round(distance, 2)
                
                # Score and rank places
                scored_places = self.scoring.rank_places(
                    places,
                    has_user_location=has_user_location,
                    top_k=30  # Get top 30 per category
                )
                
                # Filter by opening hours for this activity type
                time_range = self.TIME_SLOTS.get(activity_type)
                if time_range:
                    scored_places = self._filter_by_opening_hours(
                        scored_places, 
                        time_range[0], 
                        time_range[1]
                    )
                
                places_by_category[activity_type] = scored_places[:20]
                print(f"      Found {len(places_by_category[activity_type])} scored {activity_type} places")
            else:
                places_by_category[activity_type] = []
                print(f"      No {activity_type} places found")
        
        return places_by_category
    
    def _search_by_category_and_location(
        self, 
        categories: List[str], 
        location: str
    ) -> List[Dict[str, Any]]:
        """Search places by database category field and location"""
        try:
            query = self.supabase.client.table(self.supabase.places_table).select("*")
            
            # Build OR filter for categories
            category_filters = [f"category.ilike.%{cat}%" for cat in categories]
            
            # Add location filter
            location_filter = f"address.ilike.%{location}%"
            
            # Execute query with filters
            query = query.or_(",".join(category_filters))
            query = query.ilike("address", f"%{location}%")
            query = query.gte("rating", 3.5)  # Minimum rating
            query = query.limit(100)
            
            response = query.execute()
            
            places = []
            for place in response.data:
                # Parse coordinates
                if place.get('coordinates'):
                    coords = json.loads(place['coordinates']) if isinstance(place['coordinates'], str) else place['coordinates']
                    place['latitude'] = coords.get('lat')
                    place['longitude'] = coords.get('lon')
                places.append(place)
            
            return places
            
        except Exception as e:
            print(f"Error in category search: {e}")
            return []
    
    def _filter_by_opening_hours(
        self, 
        places: List[Dict[str, Any]], 
        start_hour: int, 
        end_hour: int
    ) -> List[Dict[str, Any]]:
        """Filter places that are likely open during the specified hours"""
        filtered = []
        
        for place in places:
            opening_hours = place.get('opening_hours')
            
            # If no opening hours data, assume it might be open (include it)
            if not opening_hours:
                filtered.append(place)
                continue
            
            # Parse opening hours (handle various formats)
            try:
                if isinstance(opening_hours, str):
                    opening_hours = json.loads(opening_hours)
                
                # Check if it's a dict with day keys
                if isinstance(opening_hours, dict):
                    # Look for any day that shows it's open during our time range
                    is_open = self._check_hours_in_range(opening_hours, start_hour, end_hour)
                    if is_open:
                        filtered.append(place)
                else:
                    # Unknown format, include it
                    filtered.append(place)
                    
            except Exception:
                # Can't parse, include place anyway
                filtered.append(place)
        
        return filtered
    
    def _check_hours_in_range(
        self, 
        hours_dict: Dict, 
        start_hour: int, 
        end_hour: int
    ) -> bool:
        """Check if any opening hours overlap with the desired time range"""
        # Common keys to check
        for key in hours_dict:
            value = hours_dict[key]
            if isinstance(value, str):
                # Try to extract hours like "8:00 - 22:00" or "08:00-22:00"
                try:
                    if 'closed' in value.lower() or 'đóng cửa' in value.lower():
                        continue
                    
                    # Extract numbers that look like hours
                    import re
                    times = re.findall(r'(\d{1,2})[:\.]?\d{0,2}', value)
                    if len(times) >= 2:
                        open_hour = int(times[0])
                        close_hour = int(times[-1])
                        
                        # Check overlap
                        if open_hour <= end_hour and close_hour >= start_hour:
                            return True
                except Exception:
                    continue
        
        # If we couldn't determine, assume open
        return True
    
    def _generate_with_gemini(
        self, 
        request: ItineraryRequest, 
        places_by_category: Dict[str, List[Dict[str, Any]]],
        weather_data: Optional[Dict[str, Any]],
        weather_summary: str
    ) -> ItineraryResponse:
        """Use Gemini to generate structured itinerary with weather awareness"""
        
        # Build enhanced prompt with scored places and weather
        places_summary = self._build_places_summary(places_by_category)
        
        weather_context = ""
        if weather_data:
            weather_context = f"""
THÔNG TIN THỜI TIẾT:
{weather_summary}

HÃY LƯU Ý:
- Nếu trời mưa, ưu tiên các địa điểm trong nhà (museum, cafe, shopping mall)
- Nếu trời nắng nóng (>32°C), tránh hoạt động ngoài trời vào buổi trưa
- Nếu trời đẹp, có thể thêm các địa điểm ngoài trời (công viên, chợ)
"""
        
        prompt = f"""Bạn là chuyên gia lập lịch trình du lịch Việt Nam thông minh.
Hãy tạo lịch trình du lịch {request.num_days} ngày tại {request.destination} với các thông tin sau:

{weather_context}

DANH SÁCH ĐỊA ĐIỂM ĐÃ ĐƯỢC XẾP HẠNG (điểm cao = tốt hơn):
{places_summary}

YÊU CẦU:
- Số ngày: {request.num_days}
- Điểm đến: {request.destination}
- Sở thích: {', '.join(request.preferences) if request.preferences else 'Khám phá tổng quát'}
- Giờ bắt đầu mỗi ngày: {request.start_time}
- Giờ kết thúc mỗi ngày: {request.end_time}

HƯỚNG DẪN QUAN TRỌNG:
1. ƯU TIÊN địa điểm có ĐIỂM SỐ CAO (score cao)
2. SẮP XẾP địa điểm GẦN NHAU trong cùng một ngày để tối ưu di chuyển
3. Mỗi ngày nên có 1 chủ đề rõ ràng (VD: "Khám phá biển", "Tham quan bảo tàng")
4. Bố trí hợp lý thời gian giữa các hoạt động
5. Chọn địa điểm PHÙ HỢP THỜI TIẾT
6. Đa dạng trải nghiệm giữa các ngày

HÃY TRẢ LỜI DẠNG JSON với format sau:
{{
  "destination": "{request.destination}",
  "num_days": {request.num_days},
  "weather_summary": "{weather_summary[:100] if weather_summary else 'N/A'}...",
  "itinerary": [
    {{
      "day": 1,
      "theme": "Khám phá trung tâm Sài Gòn",
      "activities": [
        {{
          "time": "08:00",
          "duration_minutes": 60,
          "activity_type": "breakfast",
          "place_id": "place123",
          "place_name": "Tên địa điểm",
          "address": "Địa chỉ đầy đủ",
          "latitude": 10.762622,
          "longitude": 106.660172,
          "rating": 4.5,
          "category": "Restaurant",
          "description": "Mô tả hoạt động này",
          "tips": "Lời khuyên hữu ích",
          "estimated_cost": "50,000 - 100,000 VND"
        }}
      ],
      "total_activities": 6,
      "estimated_distance_km": 15.5
    }}
  ],
  "summary": "Tổng quan lịch trình {request.num_days} ngày...",
  "total_places": 18,
  "tips": ["Mang theo ô", "Đặt trước vé"]
}}

LƯU Ý QUAN TRỌNG:
- Mỗi ngày PHẢI CÓ CHỦ ĐỀ KHÁC NHAU, KHÔNG ĐƯỢC LẶP LẠI
- Chỉ chọn địa điểm TRONG THÀNH PHỐ được yêu cầu ({request.destination}), không chọn địa điểm ở vùng lân cận
- Chỉ trả về JSON, không thêm text hay giải thích."""

        # Call Gemini with JSON response
        response_text = self.gemini.generate_with_json(prompt)
        
        # Parse JSON response
        try:
            itinerary_dict = json.loads(response_text)
            
            # Optimize routes for each day
            if 'itinerary' in itinerary_dict:
                for day in itinerary_dict['itinerary']:
                    if 'activities' in day:
                        day['activities'] = self._optimize_day_route(day['activities'])
            
            return ItineraryResponse(**itinerary_dict)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Response was: {response_text[:500]}...")
            # Fallback: create smart itinerary using scoring
            return self._create_smart_fallback_itinerary(request, places_by_category, weather_data)
    
    def _build_places_summary(self, places_by_category: Dict[str, List[Dict[str, Any]]]) -> str:
        """Build summary of scored places for Gemini prompt"""
        summary_parts = []
        
        for category, places in places_by_category.items():
            if not places:
                continue
            
            summary_parts.append(f"\n{category.upper()} (xếp theo điểm từ cao đến thấp):")
            for place in places[:10]:  # Top 10 per category
                name = place.get('name', 'N/A')
                address = place.get('address', 'N/A')
                rating = place.get('rating', 0)
                place_id = place.get('id', '')
                lat = place.get('latitude', 0)
                lon = place.get('longitude', 0)
                score = place.get('final_score', 0)
                distance = place.get('distance_km', 'N/A')
                
                summary_parts.append(
                    f"  - {name} | Score: {score:.2f} | Rating: {rating} | Distance: {distance}km | "
                    f"Address: {address} | ID: {place_id} | Lat: {lat}, Lon: {lon}"
                )
        
        return '\n'.join(summary_parts)
    
    def _optimize_day_route(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder activities to minimize travel distance using greedy nearest neighbor"""
        if len(activities) <= 2:
            return activities
        
        # Separate fixed-time activities (meals) from flexible ones
        meal_types = ['breakfast', 'lunch', 'dinner']
        meals = [a for a in activities if a.get('activity_type') in meal_types]
        others = [a for a in activities if a.get('activity_type') not in meal_types]
        
        if not others:
            return activities
        
        # Sort meals by time
        meals.sort(key=lambda x: x.get('time', '00:00'))
        
        # Optimize route for non-meal activities between meals
        optimized = []
        
        for i, meal in enumerate(meals):
            optimized.append(meal)
            
            # Find activities between this meal and the next
            current_time = meal.get('time', '00:00')
            next_meal_time = meals[i + 1].get('time', '23:59') if i + 1 < len(meals) else '23:59'
            
            # Get activities that fit in this time slot
            slot_activities = [
                a for a in others 
                if current_time < a.get('time', '12:00') < next_meal_time
            ]
            
            if slot_activities:
                # Optimize this subset using nearest neighbor
                last_lat = meal.get('latitude', 0)
                last_lon = meal.get('longitude', 0)
                
                while slot_activities:
                    nearest = min(
                        slot_activities,
                        key=lambda a: self._calculate_distance(
                            last_lat, last_lon,
                            a.get('latitude', 0), a.get('longitude', 0)
                        )
                    )
                    optimized.append(nearest)
                    slot_activities.remove(nearest)
                    last_lat = nearest.get('latitude', 0)
                    last_lon = nearest.get('longitude', 0)
        
        # Add any remaining activities
        for a in others:
            if a not in optimized:
                optimized.append(a)
        
        # Re-sort by time
        optimized.sort(key=lambda x: x.get('time', '00:00'))
        
        return optimized
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        if not all([lat1, lon1, lat2, lon2]):
            return float('inf')
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _create_smart_fallback_itinerary(
        self, 
        request: ItineraryRequest, 
        places_by_category: Dict[str, List[Dict[str, Any]]],
        weather_data: Optional[Dict[str, Any]]
    ) -> ItineraryResponse:
        """Create smart fallback itinerary using scoring instead of random"""
        days = []
        used_places = set()  # Track used places to avoid duplicates
        
        # Diverse themes for each day
        day_themes = [
            f"Khám phá bãi biển {request.destination}",
            f"Tham quan bảo tàng & di tích {request.destination}",
            f"Một ngày thư giãn tại {request.destination}",
            f"Khám phá các điểm đến mới tại {request.destination}",
            f"Trải nghiệm văn hóa địa phương {request.destination}",
            f"Ngày cuối tại {request.destination}",
        ]
        
        for day_num in range(1, request.num_days + 1):
            activities = []
            last_lat, last_lon = None, None
            
            # Alternate between beach and museum activities
            if day_num % 2 == 1:  # Odd days: beach focus
                schedule = [
                    ('beach', request.start_time or "08:00", 120),
                    ('beach', "10:30", 90),
                    ('museum', "14:00", 90),
                    ('beach', "16:30", 90),
                ]
            else:  # Even days: museum focus
                schedule = [
                    ('museum', request.start_time or "09:00", 120),
                    ('beach', "11:30", 90),
                    ('museum', "14:30", 90),
                    ('beach', "17:00", 90),
                ]
            
            for activity_type, time, duration in schedule:
                places = places_by_category.get(activity_type, [])
                
                # Filter out used places
                available = [p for p in places if p.get('id') not in used_places]
                
                if not available:
                    continue
                
                # If we have previous location, sort by proximity
                if last_lat and last_lon:
                    available.sort(
                        key=lambda p: self._calculate_distance(
                            last_lat, last_lon,
                            p.get('latitude', 0), p.get('longitude', 0)
                        )
                    )
                
                # Pick the best available place (already sorted by score, now by proximity)
                best_place = available[0]
                used_places.add(best_place.get('id'))
                
                # Weather-aware adjustments
                if weather_data and weather_data.get('main', '').lower() == 'rain':
                    # Prefer indoor activities
                    indoor_places = [p for p in available if self._is_likely_indoor(p)]
                    if indoor_places:
                        best_place = indoor_places[0]
                
                activities.append(self._create_activity(best_place, time, duration, activity_type))
                last_lat = best_place.get('latitude')
                last_lon = best_place.get('longitude')
            
            # Get theme for this day
            theme = day_themes[day_num - 1] if day_num <= len(day_themes) else f"Ngày {day_num}"
            
            day_itinerary = DayItinerary(
                day=day_num,
                theme=theme,
                activities=activities,
                total_activities=len(activities),
                estimated_distance_km=self._calculate_day_distance(activities)
            )
            days.append(day_itinerary)
        
        # Generate tips based on weather
        tips = ["Mang theo nước", "Đi giày thoải mái"]
        if weather_data:
            weather_advice = self.weather.get_weather_advice(weather_data)
            if weather_advice:
                tips.insert(0, weather_advice)
        
        return ItineraryResponse(
            destination=request.destination,
            num_days=request.num_days,
            itinerary=days,
            summary=f"Lịch trình {request.num_days} ngày khám phá {request.destination}",
            total_places=sum(len(d.activities) for d in days),
            tips=tips
        )
    
    def _is_likely_indoor(self, place: Dict[str, Any]) -> bool:
        """Check if a place is likely indoor based on category"""
        indoor_categories = ['museum', 'bảo tàng', 'cafe', 'cà phê', 'mall', 
                           'shopping', 'restaurant', 'nhà hàng']
        category = (place.get('category') or '').lower()
        name = (place.get('name') or '').lower()
        
        return any(cat in category or cat in name for cat in indoor_categories)
    
    def _calculate_day_distance(self, activities: List[ActivityDetail]) -> float:
        """Calculate total travel distance for a day"""
        total = 0.0
        for i in range(1, len(activities)):
            prev = activities[i - 1]
            curr = activities[i]
            if all([prev.latitude, prev.longitude, curr.latitude, curr.longitude]):
                total += self._calculate_distance(
                    prev.latitude, prev.longitude,
                    curr.latitude, curr.longitude
                )
        return round(total, 1)
    
    def _create_activity(self, place: Dict, time: str, duration: int, activity_type: str) -> ActivityDetail:
        """Create activity from place data"""
        return ActivityDetail(
            time=time,
            duration_minutes=duration,
            activity_type=activity_type,
            place_id=str(place.get('id', '')),
            place_name=place.get('name', 'Unknown'),
            address=place.get('address'),
            latitude=place.get('latitude'),
            longitude=place.get('longitude'),
            rating=place.get('rating'),
            category=place.get('category'),
            description=f"Tham quan {place.get('name')} - Rating: {place.get('rating', 'N/A')}",
            tips=f"Điểm đánh giá: {place.get('final_score', 0):.2f}" if place.get('final_score') else None,
            estimated_cost="100,000 - 300,000 VND"
        )
    
    @staticmethod
    def _format_budget(amount: int) -> str:
        """Format budget amount to readable string"""
        if amount >= 1000000:
            millions = amount / 1000000
            if millions == int(millions):
                return f"{int(millions)} triệu VND"
            return f"{millions:.1f} triệu VND"
        elif amount >= 1000:
            thousands = amount / 1000
            return f"{int(thousands)}k VND"
        return f"{amount:,} VND"

