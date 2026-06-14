import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuel_route.settings')
django.setup()

from route_planner.services.fuel import (
    load_fuel_prices, STATE_CENTROIDS, CANADIAN, STATE_NAMES
)
import csv
from collections import defaultdict
from django.conf import settings

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
        except:
            continue

print(f"city_prices has {len(city_prices)} entries")

fuel_stations = []
no_coords = 0

for (state, city), prices in list(city_prices.items())[:10]:
    avg_price = round(sum(prices) / len(prices), 4)
    coords = None
    centroid = STATE_CENTROIDS.get(state)
    if centroid:
        coords = list(centroid)
    print(f"{city}, {state} → coords: {coords}, price: {avg_price}")
    if coords:
        fuel_stations.append({
            "city": city,
            "state": state,
            "price": avg_price,
            "lat": coords[0],
            "lon": coords[1]
        })
    else:
        no_coords += 1

print(f"\nStations built: {len(fuel_stations)}")
print(f"No coords found: {no_coords}")


print("\n--- Calling load_fuel_prices() ---")
stations = load_fuel_prices()
print(f"Total stations returned: {len(stations)}")
if stations:
    print(f"Sample: {stations[:2]}")