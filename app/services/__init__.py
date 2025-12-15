# Services module
from app.services.supabase_client import get_supabase_client

# Lazy imports to avoid circular dependencies
def get_gemini_service():
    from app.services.gemini_service import GeminiService
    return GeminiService

def get_semantic_service():
    from app.services.semantic_service import SemanticSearchService
    return SemanticSearchService

def get_weather_service():
    from app.services.weather_service import WeatherService
    return WeatherService

def get_scoring_service():
    from app.services.scoring_service import ScoringService
    return ScoringService

def get_place_supabase_service():
    from app.services.place_supabase_service import PlaceSupabaseService
    return PlaceSupabaseService

def get_orchestrator():
    from app.services.orchestrator import ChatbotOrchestrator
    return ChatbotOrchestrator
