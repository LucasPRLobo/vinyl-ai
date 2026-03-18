"""Geocoding service: resolve city names to lat/lng coordinates.

Uses a built-in lookup table for common music cities, with Mapbox fallback.
"""

import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

# Common music cities — avoids API calls for the most frequent ones
KNOWN_CITIES: dict[str, tuple[float, float]] = {
    "New York": (40.7128, -74.0060),
    "New York City": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Detroit": (42.3314, -83.0458),
    "Memphis": (35.1495, -90.0490),
    "Nashville": (36.1627, -86.7816),
    "New Orleans": (29.9511, -90.0715),
    "Philadelphia": (39.9526, -75.1652),
    "San Francisco": (37.7749, -122.4194),
    "Seattle": (47.6062, -122.3321),
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.5200, 13.4050),
    "Munich": (48.1351, 11.5820),
    "Düsseldorf": (51.2277, 6.7735),
    "Amsterdam": (52.3676, 4.9041),
    "Brussels": (50.8503, 4.3517),
    "Stockholm": (59.3293, 18.0686),
    "Lagos": (6.5244, 3.3792),
    "Accra": (5.6037, -0.1870),
    "Johannesburg": (26.2041, 28.0473),
    "Cape Town": (-33.9249, 18.4241),
    "Addis Ababa": (9.0250, 38.7469),
    "Kinshasa": (-4.4419, 15.2663),
    "Nairobi": (-1.2921, 36.8219),
    "Kingston": (18.0179, -76.8099),
    "Havana": (23.1136, -82.3666),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "São Paulo": (-23.5505, -46.6333),
    "Salvador": (-12.9714, -38.5124),
    "Buenos Aires": (-34.6037, -58.3816),
    "Bogotá": (4.7110, -74.0721),
    "Mexico City": (19.4326, -99.1332),
    "Tokyo": (35.6762, 139.6503),
    "Osaka": (34.6937, 135.5023),
    "Seoul": (37.5665, 126.9780),
    "Mumbai": (19.0760, 72.8777),
    "Istanbul": (41.0082, 28.9784),
    "Beirut": (33.8938, 35.5018),
    "Cairo": (30.0444, 31.2357),
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Auckland": (-36.8485, 174.7633),
    "Lisbon": (38.7223, -9.1393),
    "Porto": (41.1579, -8.6291),
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3874, 2.1686),
    "Rome": (41.9028, 12.4964),
    "Milan": (45.4642, 9.1900),
    "Vienna": (48.2082, 16.3738),
    "Prague": (50.0755, 14.4378),
    "Warsaw": (52.2297, 21.0122),
    "Moscow": (55.7558, 37.6173),
    "Manchester": (53.4808, -2.2426),
    "Bristol": (51.4545, -2.5879),
    "Liverpool": (53.4084, -2.9916),
    "Dakar": (14.7167, -17.4677),
    "Bamako": (12.6392, -8.0029),
    "Abidjan": (5.3600, -4.0083),
    "Taipei": (25.0330, 121.5654),
    "Shanghai": (31.2304, 121.4737),
    "Beijing": (39.9042, 116.4074),
    "Bangkok": (13.7563, 100.5018),
    "Jakarta": (-6.2088, 106.8456),
    "Englewood Cliffs": (40.8834, -73.9526),  # Rudy Van Gelder's studio
    "Hackensack": (40.8859, -74.0435),  # Van Gelder studio original location
    "Cincinnati": (39.1031, -84.5120),
    "Minneapolis": (44.9778, -93.2650),
    "Atlanta": (33.7490, -84.3880),
    "Houston": (29.7604, -95.3698),
    "Cleveland": (41.4993, -81.6944),
    "St. Louis": (38.6270, -90.1994),
    "Pittsburgh": (40.4406, -79.9959),
}


async def geocode_city(city_name: str) -> tuple[float, float] | None:
    """Resolve a city name to (lat, lng). Uses local lookup first, then Mapbox API."""
    # Check local lookup
    if city_name in KNOWN_CITIES:
        return KNOWN_CITIES[city_name]

    # Normalize and try again
    normalized = city_name.strip().title()
    if normalized in KNOWN_CITIES:
        return KNOWN_CITIES[normalized]

    # Mapbox fallback
    if not settings.mapbox_access_token:
        logger.warning(f"Cannot geocode '{city_name}': no Mapbox token configured")
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.mapbox.com/geocoding/v5/mapbox.places/{city_name}.json",
                params={"access_token": settings.mapbox_access_token, "limit": 1, "types": "place"},
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if features:
                lng, lat = features[0]["center"]
                # Cache it
                KNOWN_CITIES[city_name] = (lat, lng)
                return (lat, lng)
    except Exception as e:
        logger.error(f"Geocoding failed for '{city_name}': {e}")

    return None


def geocode_city_sync(city_name: str) -> tuple[float, float] | None:
    """Synchronous version using only the local lookup table."""
    if city_name in KNOWN_CITIES:
        return KNOWN_CITIES[city_name]
    normalized = city_name.strip().title()
    return KNOWN_CITIES.get(normalized)
