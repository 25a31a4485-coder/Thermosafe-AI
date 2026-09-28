"""
Centralized Geographic Boundaries and Geospatial Validation for India.
ThermoSafe AI strictly enforces India-Only observation scope.
"""
from typing import Tuple

# India territorial bounding box (Mainland, Lakshadweep, Andaman & Nicobar Islands)
# Latitudes:  6.0° N to 37.5° N
# Longitudes: 68.0° E to 97.5° E
INDIA_LAT_MIN: float = 6.0
INDIA_LAT_MAX: float = 37.5
INDIA_LON_MIN: float = 68.0
INDIA_LON_MAX: float = 97.5

# Bounding box formatted for NASA FIRMS area CSV API (min_lon,min_lat,max_lon,max_lat)
INDIA_BBOX_CSV: str = f"{INDIA_LON_MIN},{INDIA_LAT_MIN},{INDIA_LON_MAX},{INDIA_LAT_MAX}"
INDIA_COUNTRY_CODE: str = "IND"


def is_inside_india(latitude: float, longitude: float) -> bool:
    """
    Validates whether geographic coordinates fall strictly within India's sovereign territorial bounds.
    Rejects any points outside mainland India, Andaman & Nicobar Islands, or Lakshadweep.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        return (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX) and (INDIA_LON_MIN <= lon <= INDIA_LON_MAX)
    except (ValueError, TypeError):
        return False


def clamp_to_india(latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Clamps coordinates to the India bounding box if slightly out of bounds.
    """
    lat = max(INDIA_LAT_MIN, min(INDIA_LAT_MAX, float(latitude)))
    lon = max(INDIA_LON_MIN, min(INDIA_LON_MAX, float(longitude)))
    return lat, lon
