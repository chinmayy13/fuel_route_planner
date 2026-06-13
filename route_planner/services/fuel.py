import csv
import math
import os
from django.conf import settings


def load_fuel_prices():

    city_coordinates = {
        ("Alabama", "Birmingham"): (33.5186, -86.8104),
        ("Arizona", "Phoenix"): (33.4484, -112.0740),
        ("Arizona", "Flagstaff"): (35.1983, -111.6513),
        ("Arkansas", "Little Rock"): (34.7465, -92.2896),
        ("California", "Los Angeles"): (34.0522, -118.2437),
        ("California", "San Francisco"): (37.7749, -122.4194),
        ("California", "Barstow"): (34.8958, -117.0228),
        ("Colorado", "Denver"): (39.7392, -104.9903),
        ("Colorado", "Grand Junction"): (39.0639, -108.5506),
        ("Florida", "Miami"): (25.7617, -80.1918),
        ("Florida", "Orlando"): (28.5383, -81.3792),
        ("Florida", "Jacksonville"): (30.3322, -81.6557),
        ("Georgia", "Atlanta"): (33.7490, -84.3880),
        ("Illinois", "Chicago"): (41.8781, -87.6298),
        ("Illinois", "Springfield"): (39.7817, -89.6501),
        ("Indiana", "Indianapolis"): (39.7684, -86.1581),
        ("Kansas", "Wichita"): (37.6872, -97.3301),
        ("Kansas", "Kansas City"): (39.1141, -94.6275),
        ("Kentucky", "Louisville"): (38.2527, -85.7585),
        ("Louisiana", "New Orleans"): (29.9511, -90.0715),
        ("Maryland", "Baltimore"): (39.2904, -76.6122),
        ("Massachusetts", "Boston"): (42.3601, -71.0589),
        ("Michigan", "Detroit"): (42.3314, -83.0458),
        ("Minnesota", "Minneapolis"): (44.9778, -93.2650),
        ("Mississippi", "Jackson"): (32.2988, -90.1848),
        ("Missouri", "Saint Louis"): (38.6270, -90.1994),
        ("Missouri", "Kansas City"): (39.0997, -94.5786),
        ("Montana", "Billings"): (45.7833, -108.5007),
        ("Nebraska", "Omaha"): (41.2565, -95.9345),
        ("Nevada", "Las Vegas"): (36.1699, -115.1398),
        ("Nevada", "Reno"): (39.5296, -119.8138),
        ("New Jersey", "Newark"): (40.7357, -74.1724),
        ("New Mexico", "Albuquerque"): (35.0844, -106.6504),
        ("New York", "New York City"): (40.7128, -74.0060),
        ("New York", "Buffalo"): (42.8864, -78.8784),
        ("North Carolina", "Charlotte"): (35.2271, -80.8431),
        ("Ohio", "Columbus"): (39.9612, -82.9988),
        ("Ohio", "Cleveland"): (41.4993, -81.6944),
        ("Oklahoma", "Oklahoma City"): (35.4676, -97.5164),
        ("Oklahoma", "Tulsa"): (36.1540, -95.9928),
        ("Oregon", "Portland"): (45.5051, -122.6750),
        ("Pennsylvania", "Philadelphia"): (39.9526, -75.1652),
        ("Pennsylvania", "Pittsburgh"): (40.4406, -79.9959),
        ("Tennessee", "Nashville"): (36.1627, -86.7816),
        ("Tennessee", "Memphis"): (35.1495, -90.0490),
        ("Texas", "Houston"): (29.7604, -95.3698),
        ("Texas", "Dallas"): (32.7767, -96.7970),
        ("Texas", "San Antonio"): (29.4241, -98.4936),
        ("Texas", "Amarillo"): (35.2220, -101.8313),
        ("Texas", "El Paso"): (31.7619, -106.4850),
        ("Utah", "Salt Lake City"): (40.7608, -111.8910),
        ("Virginia", "Richmond"): (37.5407, -77.4360),
        ("Washington", "Seattle"): (47.6062, -122.3321),
        ("Washington", "Spokane"): (47.6588, -117.4260),
        ("Wisconsin", "Milwaukee"): (43.0389, -87.9065),
        ("Wyoming", "Cheyenne"): (41.1400, -104.8202),
        ("Wyoming", "Casper"): (42.8501, -106.3252),
    }

    fuel_stations = []

    with open(settings.FUEL_PRICES_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            state = row["State"]
            city = row["City"]
            price = float(row["Fuel_Price_Per_Gallon"])
            coords = city_coordinates.get((state, city))
            if coords:
                fuel_stations.append({
                    "state": state,
                    "city": city,
                    "price": price,
                    "lat": coords[0],
                    "lon": coords[1]
                })

    return fuel_stations


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates distance in miles between two GPS coordinates.
    Uses the Haversine formula — standard formula for GPS distances.
    
    Think of it as: straight line distance between two points on Earth.
    """
    R = 3958.8 

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c 


def find_nearest_stations(lat, lon, fuel_stations, max_distance_miles=150):
    nearby = []
    
    for station in fuel_stations:
        dist = haversine_distance(lat, lon, station["lat"], station["lon"])
        if dist <= max_distance_miles:
            nearby.append({**station, "distance_from_route": round(dist, 1)})

    nearby.sort(key=lambda x: x["price"])
    
    return nearby

