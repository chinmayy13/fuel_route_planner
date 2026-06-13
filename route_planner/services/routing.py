import requests
from django.conf import settings


def geocode_location(place_name):
    url = "https://api.openrouteservice.org/geocode/search"
    
    params = {
        "api_key": settings.ORS_API_KEY,
        "text": place_name,
        "boundary.country": "US",   
        "size": 1                   
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status() 
    
    data = response.json()
    
    features = data.get("features", [])
    if not features:
        raise ValueError(f"Could not find location: {place_name}")
    
    coords = features[0]["geometry"]["coordinates"]
    lon, lat = coords[0], coords[1]
    
    return lat, lon


def get_route(start_place, finish_place):
    
    start_lat, start_lon = geocode_location(start_place)
    finish_lat, finish_lon = geocode_location(finish_place)
    
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "coordinates": [
            [start_lon, start_lat],
            [finish_lon, finish_lat]
        ]
    }
    
    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    feature = data["features"][0]
    props = feature["properties"]
    segments = props["segments"][0]
    
    distance_meters = segments["distance"]
    distance_miles = distance_meters * 0.000621371
    
    duration_seconds = segments["duration"]
    duration_hours = duration_seconds / 3600
    
    raw_coords = feature["geometry"]["coordinates"]
    coordinates = [(c[1], c[0]) for c in raw_coords]
    
    return {
        "distance_miles": round(distance_miles, 2),
        "duration_hours": round(duration_hours, 2),
        "coordinates": coordinates,
        "start_coords": (start_lat, start_lon),
        "finish_coords": (finish_lat, finish_lon)
    }


def sample_waypoints(coordinates, distance_miles, interval_miles=None):
    from django.conf import settings
    if interval_miles is None:
        interval_miles = settings.VEHICLE_MAX_RANGE_MILES * 0.8

    if not coordinates:
        return []

    waypoints = []
    total_points = len(coordinates)
    points_per_mile = total_points / distance_miles
    points_per_interval = int(points_per_mile * interval_miles)

    for i in range(points_per_interval, total_points, points_per_interval):
        miles_remaining = (total_points - i) / points_per_mile
        if miles_remaining > 50:
            waypoints.append({
                "mile_marker": round(i / points_per_mile),
                "lat": coordinates[i][0],
                "lon": coordinates[i][1]
            })

    return waypoints