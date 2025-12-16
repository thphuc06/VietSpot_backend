import os
import tempfile
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    HttpOptions,
    Tool,
)
from app.core.config import settings
from app.schemas.chat import QueryClassification
import json
import re


class GeminiService:
    def __init__(self):
        # Setup Google Cloud credentials from environment variable (for Railway/Cloud deployment)
        self._setup_credentials()
        
        # Setup Vertex AI
        os.environ["GOOGLE_CLOUD_PROJECT"] = settings.VERTEX_PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = settings.VERTEX_LOCATION
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
        
        # Create Vertex AI client
        self.client = genai.Client(http_options=HttpOptions(api_version="v1"))
        self.model_id = settings.VERTEX_MODEL_ID
        
        # Tools for grounding
        self.grounding_tools = [Tool(google_search=GoogleSearch())]
    
    def _setup_credentials(self):
        """Setup Google Cloud credentials from environment variable"""
        # Check if credentials JSON is provided as environment variable
        credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        
        if credentials_json:
            # Write credentials to a temporary file
            try:
                # Create a temporary file for credentials
                fd, path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as f:
                    f.write(credentials_json)
                
                # Set the path for Google libraries to find
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                print(f"✅ Loaded Google credentials from environment variable")
            except Exception as e:
                print(f"⚠️ Error setting up credentials: {e}")
        else:
            # Check if already set via file path
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                print(f"✅ Using existing GOOGLE_APPLICATION_CREDENTIALS")
            else:
                print(f"⚠️ No Google credentials found. Vertex AI may not work.")
    
    def _clean_text(self, text: str) -> str:
        """Remove control characters and clean text"""
        if not text:
            return ''
        # Remove control characters except space, tab (keep tab for formatting)
        text = ''.join(char if ord(char) >= 32 or char in ['\t'] else ' ' for char in text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string - just strip whitespace, json.loads() handles escapes"""
        if not json_str:
            return json_str
        return json_str.strip()
        
    def classify_query(self, user_prompt: str) -> QueryClassification:
        """
        Classify user query and extract relevant information
        Returns query type: general_query, nearby_search, or specific_search
        """
        
        classification_prompt = f"""
Phân tích câu hỏi của người dùng và trả về thông tin dưới dạng JSON với cấu trúc sau:

{{
    "query_type": "general_query" hoặc "nearby_search" hoặc "specific_search",
    "keywords": ["từ khóa 1", "từ khóa 2", ...],
    "location_mentioned": "tên địa điểm chuẩn hóa (đã sửa lỗi chính tả) nếu có, null nếu không",
    "city": "tên thành phố/tỉnh đã chuẩn hóa (ví dụ: 'Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng'), null nếu không có",
    "district": "tên quận/huyện/phường đã chuẩn hóa (ví dụ: 'Quận 1', 'Bình Thạnh', 'Hoàn Kiếm'), null nếu không có",
    "min_rating": số rating tối thiểu (1.0-5.0) nếu người dùng yêu cầu, null nếu không,
    "max_rating": số rating tối đa (1.0-5.0) nếu người dùng yêu cầu, null nếu không,
    "price_range": "cheap/moderate/expensive nếu có đề cập, null nếu không",
    "category": "loại hình địa điểm (restaurant, cafe, hotel, tourist_attraction, etc.) nếu có, null nếu không",
    "radius_km": số km nếu người dùng đề cập (ví dụ: "gần tôi 2km" -> 2), null nếu không,
    "number_of_places": số lượng địa điểm nếu người dùng yêu cầu, null nếu không,
    "vietnamese_query": "câu hỏi đã dịch sang tiếng Việt chuẩn (dùng cho semantic search)",
    "corrected_query": "câu hỏi đã được sửa lỗi chính tả (giữ nguyên ngôn ngữ gốc)",
    "original_language": "ngôn ngữ gốc của câu hỏi: 'vi' (tiếng Việt), 'en' (English), 'zh' (Chinese), etc."
}}

Quy tắc phân loại (QUAN TRỌNG - ưu tiên theo thứ tự):
1. "general_query": Câu hỏi chung, không liên quan đến địa điểm cụ thể

2. "nearby_search": ƯU TIÊN CAO NHẤT - Khi có BẤT KỲ từ nào sau: "gần tôi", "gần đây", "xung quanh", "quanh đây", "nearby", "around me", "trong vòng", "cách tôi"

3. "specific_search": CHỈ khi có ĐỊA ĐIỂM CỤ THỂ (tên thành phố/quận) VÀ KHÔNG có "gần tôi"

Câu hỏi của người dùng: "{user_prompt}"

Chỉ trả về JSON, không thêm giải thích.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=classification_prompt
            )
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            classification_data = json.loads(result_text)
            return QueryClassification(**classification_data)
            
        except Exception as e:
            print(f"Error in classify_query: {e}")
            # Fallback
            return QueryClassification(
                query_type="specific_search",
                keywords=[],
                vietnamese_query=user_prompt,
                corrected_query=user_prompt
            )
    
    def answer_general_query(self, user_prompt: str) -> str:
        """
        Answer general queries with Google Search Grounding for realtime info
        """
        general_prompt = f"""
Bạn là trợ lý du lịch thông minh của VietSpot. Hãy trả lời câu hỏi sau một cách thân thiện và hữu ích:

Câu hỏi: {user_prompt}

Trả lời bằng tiếng Việt, ngắn gọn và dễ hiểu.
"""
        try:
            print(f"🔍 Using Google Search Grounding for general query...")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=general_prompt,
                config=GenerateContentConfig(
                    tools=self.grounding_tools
                )
            )
            return response.text
        except Exception as e:
            print(f"Error in answer_general_query: {e}")
            return "Xin lỗi, tôi không thể trả lời câu hỏi này lúc này. Vui lòng thử lại."
    
    def select_places_and_generate_response(
        self, 
        user_prompt: str, 
        places: list, 
        max_places: int = 5,
        weather_data: dict = None,
        original_language: str = "vi"
    ) -> tuple[list, str]:
        """
        Let Gemini select relevant places AND generate final response in ONE request
        Responds in the user's original language
        Returns: (selected_places, answer_text)
        """
        if not places:
            return [], "Xin lỗi, tôi không tìm thấy địa điểm nào phù hợp với yêu cầu của bạn."
        
        # Prepare places information for Gemini
        places_info = []
        for idx, place in enumerate(places):
            about_text = place.get('about', '')
            if isinstance(about_text, dict):
                about_text = str(about_text)
            elif about_text is None:
                about_text = ''
            else:
                about_text = str(about_text)
            
            about_text = self._clean_text(about_text)[:200]
            
            place_info = {
                "index": idx,
                "id": place.get('id', f'place_{idx}'),
                "name": self._clean_text(str(place.get('name', 'N/A'))),
                "address": self._clean_text(str(place.get('address', 'Không có thông tin'))),
                "category": self._clean_text(str(place.get('category', 'Không rõ'))),
                "rating": place.get('rating', 'N/A'),
                "rating_count": place.get('rating_count', 'N/A'),
                "price_level": self._clean_text(str(place.get('price_level', 'Không rõ'))),
                "distance_km": place.get('distance_km', 'N/A'),
                "phone": self._clean_text(str(place.get('phone', 'N/A'))),
                "website": self._clean_text(str(place.get('website', 'N/A'))),
                "opening_hours": self._clean_text(str(place.get('opening_hours', 'N/A'))),
                "about": about_text
            }
            places_info.append(place_info)
        
        places_json = json.dumps(places_info, ensure_ascii=False, indent=2)
        
        weather_text = ""
        if weather_data:
            weather_text = f"""
Thông tin thời tiết hiện tại:
- Nhiệt độ: {weather_data.get('temp', 'N/A')}°C
- Cảm giác như: {weather_data.get('feels_like', 'N/A')}°C
- Mô tả: {weather_data.get('description', 'N/A')}
- Độ ẩm: {weather_data.get('humidity', 'N/A')}%
"""
        
        # Determine response language based on original_language
        language_instruction = "Trả lời bằng tiếng Việt tự nhiên, thân thiện"
        if original_language == "en":
            language_instruction = "Respond in natural, friendly English"
        elif original_language == "zh":
            language_instruction = "用自然友好的中文回答"
        elif original_language == "ja":
            language_instruction = "自然で親しみやすい日本語で回答してください"
        elif original_language == "ko":
            language_instruction = "자연스럽고 친근한 한국어로 답변하세요"
        elif original_language != "vi":
            language_instruction = f"Respond in the user's language ({original_language}), naturally and friendly"
        
        combined_prompt = f"""
Bạn là trợ lý du lịch thông minh VietSpot. Nhiệm vụ của bạn:
1. CHỌN các địa điểm PHÙ HỢP NHẤT từ danh sách
2. TẠO câu trả lời tự nhiên, thân thiện giới thiệu các địa điểm đã chọn

Câu hỏi của người dùng: "{user_prompt}"

Danh sách địa điểm ứng viên ({len(places_info)} địa điểm):
{places_json}

{weather_text}

BƯỚC 1: CHỌN ĐỊA ĐIỂM
- Chọn TỐI ĐA {max_places} địa điểm phù hợp nhất
- Ưu tiên: đánh giá cao, thông tin rõ ràng, gần người dùng, phù hợp ngữ cảnh

BƯỚC 2: TẠO CÂU TRẢ LỜI
- {language_instruction}
- Sử dụng markdown với **bold** cho tên địa điểm

Trả về JSON với cấu trúc:
{{
    "selected_indices": [0, 2, 5, ...],
    "answer": "Câu trả lời chi tiết giới thiệu các địa điểm..."
}}

Chỉ trả về JSON, không thêm giải thích.
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=combined_prompt
            )
            result_text = response.text.strip()
            print(f"📥 Raw Gemini response (first 300 chars): {result_text[:300]}")
            
            # Try multiple JSON extraction methods
            json_text = None
            
            # Method 1: Extract from ```json ... ``` blocks
            json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', result_text, re.MULTILINE)
            if json_match:
                json_text = json_match.group(1)
            
            # Method 2: Extract from ``` ... ``` blocks
            if not json_text:
                json_match = re.search(r'```\s*(\{[\s\S]*?\})\s*```', result_text, re.MULTILINE)
                if json_match:
                    json_text = json_match.group(1)
            
            # Method 3: Use entire response if it looks like JSON
            if not json_text and result_text.startswith('{'):
                brace_count = 0
                for i, char in enumerate(result_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_text = result_text[:i+1]
                            break
            
            # Method 4: Find first JSON object in text
            if not json_text:
                start = result_text.find('{')
                if start != -1:
                    brace_count = 0
                    for i in range(start, len(result_text)):
                        if result_text[i] == '{':
                            brace_count += 1
                        elif result_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_text = result_text[start:i+1]
                                break
            
            if not json_text:
                raise ValueError("Could not extract valid JSON from response")
            
            json_text = self._clean_json_string(json_text.strip())
            
            result_data = json.loads(json_text)
            selected_indices = result_data.get('selected_indices', [])
            answer = result_data.get('answer', '')
            
            print(f"🤖 Gemini selected {len(selected_indices)} places and generated response")
            
            # Return selected places
            selected_places = []
            for idx in selected_indices:
                if 0 <= idx < len(places):
                    selected_places.append(places[idx])
            
            # If no valid selection, return top places
            if not selected_places:
                print("⚠️ No valid selection, returning top places")
                selected_places = places[:max_places]
            
            if not answer:
                answer = "Dưới đây là các địa điểm gợi ý cho bạn."
            
            return selected_places, answer
            
        except Exception as e:
            print(f"❌ Error in select_places_and_generate_response: {e}")
            return places[:max_places], "Dưới đây là các địa điểm gợi ý cho bạn."
