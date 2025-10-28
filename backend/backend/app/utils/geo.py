from math import radians, sin, cos, sqrt, atan2

def calc_distance(lat1, lng1, lat2, lng2):
    """Return distance in km between two lat/lng coordinates."""
    if not all([lat1, lng1, lat2, lng2]):
        return None
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return round(R * 2 * atan2(sqrt(a), sqrt(1-a)), 2)
