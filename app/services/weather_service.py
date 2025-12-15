import requests
from app.core.config import settings
from typing import Dict, Any, Optional


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_weather_by_coords(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get weather data for specific coordinates
        """
        if not self.api_key:
            print("Warning: OPENWEATHER_API_KEY not set")
            return None
            
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',  # Celsius
                'lang': 'vi'  # Vietnamese
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_info = {
                'temp': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'main': data['weather'][0]['main'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all']
            }
            
            return weather_info
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
        except Exception as e:
            print(f"Error processing weather data: {e}")
            return None
    
    def get_weather_by_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Get weather data for a specific city
        """
        if not self.api_key:
            print("Warning: OPENWEATHER_API_KEY not set")
            return None
            
        try:
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather_info = {
                'temp': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'main': data['weather'][0]['main'],
                'icon': data['weather'][0]['icon'],
                'wind_speed': data['wind']['speed'],
                'clouds': data['clouds']['all'],
                'coords': {
                    'lat': data['coord']['lat'],
                    'lon': data['coord']['lon']
                }
            }
            
            return weather_info
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
        except Exception as e:
            print(f"Error processing weather data: {e}")
            return None
    
    def get_weather_advice(self, weather_info: Dict[str, Any]) -> str:
        """
        Generate weather advice based on conditions
        """
        if not weather_info:
            return ""
        
        temp = weather_info.get('temp', 0)
        main = weather_info.get('main', '').lower()
        humidity = weather_info.get('humidity', 0)
        
        advice = []
        
        # Temperature advice
        if temp < 15:
            advice.append("Thời tiết khá lạnh, nên mang theo áo ấm.")
        elif temp > 32:
            advice.append("Thời tiết nóng, nên mang theo nước uống và kem chống nắng.")
        elif temp > 28:
            advice.append("Thời tiết khá nóng, nên mặc quần áo thoáng mát.")
        
        # Weather condition advice
        if 'rain' in main:
            advice.append("Trời mưa, nên mang theo ô hoặc áo mưa.")
        elif 'cloud' in main and humidity > 80:
            advice.append("Trời nhiều mây và độ ẩm cao, có thể sẽ mưa.")
        
        return " ".join(advice) if advice else "Thời tiết tốt cho việc du lịch."
