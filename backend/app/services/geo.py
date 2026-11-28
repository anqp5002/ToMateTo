"""Distance calculations; never persist or send a viewer's coordinates."""

from math import asin, cos, radians, sin, sqrt


def distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance on a spherical Earth, including across the dateline."""
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    term = (
        sin(delta_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon / 2) ** 2
    )
    return 2 * 6_371_000 * asin(sqrt(min(1.0, max(0.0, term))))
