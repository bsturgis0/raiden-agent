import os
import requests
from typing import Optional
from langchain_core.tools import tool

def _get_weather_api_key() -> Optional[str]:
    return os.getenv("OPENWEATHERMAP_API_KEY")

@tool
def get_weather(location: str) -> str:
    """Gets current weather and forecast for a location."""
    api_key = _get_weather_api_key()
    if not api_key:
        return "Error: OpenWeatherMap API key not configured"
        
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    try:
        response = requests.get(f"{base_url}?q={location}&appid={api_key}&units=metric")
        data = response.json()
        
        if response.status_code == 200:
            weather = {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"]
            }
            return f"Weather in {location}:\n" + \
                   f"Temperature: {weather['temperature']}°C\n" + \
                   f"Feels like: {weather['feels_like']}°C\n" + \
                   f"Humidity: {weather['humidity']}%\n" + \
                   f"Conditions: {weather['description']}\n" + \
                   f"Wind speed: {weather['wind_speed']} m/s"
        else:
            return f"Error getting weather: {data.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_location_info(coordinates: str) -> str:
    """Gets information about a geographic location using coordinates (lat,lon)."""
    api_key = _get_weather_api_key()
    if not api_key:
        return "Error: OpenWeatherMap API key not configured"
        
    try:
        lat, lon = map(float, coordinates.split(","))
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data:
            location = data[0]
            return f"Location Information:\n" + \
                   f"Name: {location.get('name')}\n" + \
                   f"Country: {location.get('country')}\n" + \
                   f"State: {location.get('state', 'N/A')}\n" + \
                   f"Coordinates: {lat}, {lon}"
        else:
            return "Error: Location not found"
            
    except ValueError:
        return "Error: Invalid coordinates format. Use 'latitude,longitude'"
    except Exception as e:
        return f"Error: {str(e)}"
