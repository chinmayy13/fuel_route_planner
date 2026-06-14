import csv
import math
import json
import os
import hashlib
from collections import defaultdict
from django.conf import settings

CANADIAN = {'AB', 'BC', 'MB', 'NB', 'NS', 'ON', 'QC', 'SK', 'YT'}

STATE_NAMES = {
    'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas',
    'CA':'California','CO':'Colorado','CT':'Connecticut','DE':'Delaware',
    'FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho',
    'IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas',
    'KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland',
    'MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi',
    'MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada',
    'NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York',
    'NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma',
    'OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina',
    'SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah',
    'VT':'Vermont','VA':'Virginia','WA':'Washington','WV':'West Virginia',
    'WI':'Wisconsin','WY':'Wyoming'
}

STATE_BOUNDS = {
    'AL': (30.1, 35.0, -88.5, -84.9), 'AR': (33.0, 36.5, -94.6, -89.6),
    'AZ': (31.3, 37.0, -114.8, -109.0), 'CA': (32.5, 42.0, -124.4, -114.1),
    'CO': (37.0, 41.0, -109.1, -102.0), 'CT': (40.9, 42.1, -73.7, -71.8),
    'DE': (38.4, 39.8, -75.8, -75.0), 'FL': (24.5, 31.0, -87.6, -80.0),
    'GA': (30.4, 35.0, -85.6, -80.8), 'IA': (40.4, 43.5, -96.6, -90.1),
    'ID': (42.0, 49.0, -117.2, -111.0), 'IL': (36.9, 42.5, -91.5, -87.5),
    'IN': (37.8, 41.8, -88.1, -84.8), 'KS': (37.0, 40.0, -102.1, -94.6),
    'KY': (36.5, 39.1, -89.6, -81.9), 'LA': (28.9, 33.0, -94.0, -88.8),
    'MA': (41.2, 42.9, -73.5, -69.9), 'MD': (37.9, 39.7, -79.5, -75.0),
    'ME': (43.1, 47.5, -71.1, -66.9), 'MI': (41.7, 48.3, -90.4, -82.4),
    'MN': (43.5, 49.4, -97.2, -89.5), 'MO': (36.0, 40.6, -95.8, -89.1),
    'MS': (30.2, 35.0, -91.7, -88.1), 'MT': (44.4, 49.0, -116.1, -104.0),
    'NC': (33.8, 36.6, -84.3, -75.5), 'ND': (45.9, 49.0, -104.1, -96.6),
    'NE': (40.0, 43.0, -104.1, -95.3), 'NH': (42.7, 45.3, -72.6, -70.6),
    'NJ': (38.9, 41.4, -75.6, -73.9), 'NM': (31.3, 37.0, -109.1, -103.0),
    'NV': (35.0, 42.0, -120.0, -114.0), 'NY': (40.5, 45.0, -79.8, -71.9),
    'OH': (38.4, 42.3, -84.8, -80.5), 'OK': (33.6, 37.0, -103.0, -94.4),
    'OR': (42.0, 46.3, -124.6, -116.5), 'PA': (39.7, 42.3, -80.5, -74.7),
    'RI': (41.1, 42.0, -71.9, -71.1), 'SC': (32.0, 35.2, -83.4, -78.5),
    'SD': (42.5, 45.9, -104.1, -96.4), 'TN': (35.0, 36.7, -90.3, -81.6),
    'TX': (25.8, 36.5, -106.6, -93.5), 'UT': (37.0, 42.0, -114.1, -109.0),
    'VA': (36.5, 39.5, -83.7, -75.2), 'VT': (42.7, 45.0, -73.4, -71.5),
    'WA': (45.5, 49.0, -124.8, -116.9), 'WI': (42.5, 47.1, -92.9, -86.8),
    'WV': (37.2, 40.6, -82.6, -77.7), 'WY': (41.0, 45.0, -111.1, -104.1),
}

COORDS_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'city_coords_cache.json'
)


def load_city_coords_cache():
    if os.path.exists(COORDS_CACHE_FILE):
        with open(COORDS_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def city_to_coords(city, state):
    bounds = STATE_BOUNDS.get(state)
    if not bounds:
        return None

    min_lat, max_lat, min_lon, max_lon = bounds


    h = hashlib.md5(f"{city}{state}".encode()).hexdigest()
    lat_frac = int(h[:8], 16) / 0xffffffff
    lon_frac = int(h[8:16], 16) / 0xffffffff

    lat = round(min_lat + lat_frac * (max_lat - min_lat), 5)
    lon = round(min_lon + lon_frac * (max_lon - min_lon), 5)

    return lat, lon


def load_fuel_prices():
    city_coords_cache = load_city_coords_cache()


    city_prices = defaultdict(list)
    with open(settings.FUEL_PRICES_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                city = row['City'].strip()
                state = row['State'].strip()
                price = float(row['Retail Price'])
                if state not in CANADIAN and state in STATE_NAMES:
                    city_prices[(state, city)].append(price)
            except (ValueError, KeyError):
                continue

    fuel_stations = []
    for (state, city), prices in city_prices.items():
        avg_price = round(sum(prices) / len(prices), 4)
        cache_key = f"{state}|{city}"

        cached = city_coords_cache.get(cache_key)
        if cached:
            lat, lon = cached[0], cached[1]
            coords_type = "exact"
        else:
            coords = city_to_coords(city, state)
            if not coords:
                continue
            lat, lon = coords
            coords_type = "approximate"

        fuel_stations.append({
            "state": state,
            "state_name": STATE_NAMES.get(state, state),
            "city": city,
            "price": avg_price,
            "lat": lat,
            "lon": lon,
            "coords_type": coords_type
        })

    return fuel_stations


def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance in miles between two GPS points using Haversine formula."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def find_nearest_stations(lat, lon, fuel_stations, max_distance_miles=150):
    """
    Find all stations within range of a route point.
    Returns sorted cheapest first.
    """
    nearby = []
    for station in fuel_stations:
        dist = haversine_distance(lat, lon, station["lat"], station["lon"])
        if dist <= max_distance_miles:
            nearby.append({**station, "distance_from_route": round(dist, 1)})
    nearby.sort(key=lambda x: x["price"])
    return nearby