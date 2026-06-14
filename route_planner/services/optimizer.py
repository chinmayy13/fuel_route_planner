from .fuel import load_fuel_prices, find_nearest_stations, haversine_distance
from django.conf import settings

interval_miles = settings.VEHICLE_MAX_RANGE_MILES * 0.8
def optimize_fuel_stops(route_data):
    """
    Greedy fuel optimization strategy:
    At each waypoint, the cheapest nearby station is selected.

    Note: This is a greedy approach, not global optimization.
    A globally optimal solution would look ahead and buy more
    fuel at cheaper stations before expensive regions.
    The greedy approach works well in practice and runs in O(n)
    time where n = number of waypoints.
    """

    fuel_stations = load_fuel_prices()

    waypoints = route_data["waypoints"]
    total_distance = route_data["distance_miles"]
    mpg = settings.VEHICLE_MPG
    max_range = settings.VEHICLE_MAX_RANGE_MILES

    fuel_stops = []
    total_fuel_cost = 0.0

    all_waypoints = waypoints.copy()

    for waypoint in all_waypoints:
        lat = waypoint["lat"]
        lon = waypoint["lon"]
        mile_marker = waypoint["mile_marker"]


        # nearby_stations = find_nearest_stations(lat, lon, fuel_stations)
        nearby_stations = find_nearest_stations(lat, lon, fuel_stations, max_distance_miles=100)

        if not nearby_stations:
            continue

        best_station = nearby_stations[0]

        miles_this_leg = min(interval_miles, total_distance - mile_marker)

        if miles_this_leg <= 0:
            continue

        gallons_needed = miles_this_leg / mpg

        leg_cost = round(gallons_needed * best_station["price"], 2)
        total_fuel_cost += leg_cost

        fuel_stops.append({
            "stop_number": len(fuel_stops) + 1,
            "mile_marker": mile_marker,
            "city": best_station["city"],
            "state": best_station["state"],
            "fuel_price_per_gallon": best_station["price"],
            "gallons_to_fill": round(gallons_needed, 2),
            "cost_at_this_stop": leg_cost,
            "station_distance_from_route": best_station["distance_from_route"],
            "coordinates": {
                "lat": best_station["lat"],
                "lon": best_station["lon"]
            }
        })

    if fuel_stops:
        last_mile = fuel_stops[-1]["mile_marker"]
        final_leg_miles = total_distance - last_mile

        if final_leg_miles > 0:
            final_gallons = final_leg_miles / mpg

            finish_lat = route_data["finish_coords"][0]
            finish_lon = route_data["finish_coords"][1]
            nearby = find_nearest_stations(
                finish_lat, finish_lon, fuel_stations, max_distance_miles=100
            )

            if nearby:
                last_station = nearby[0]
                final_cost = round(final_gallons * last_station["price"], 2)
                total_fuel_cost += final_cost

                fuel_stops.append({
                    "stop_number": len(fuel_stops) + 1,
                    "mile_marker": round(last_mile + final_leg_miles),
                    "city": last_station["city"],
                    "state": last_station["state"],
                    "fuel_price_per_gallon": last_station["price"],
                    "gallons_to_fill": round(final_gallons, 2),
                    "cost_at_this_stop": final_cost,
                    "station_distance_from_route": last_station[
                        "distance_from_route"
                    ],
                    "coordinates": {
                        "lat": last_station["lat"],
                        "lon": last_station["lon"]
                    }
                })

    return {
        "fuel_stops": fuel_stops,
        "total_fuel_cost": round(total_fuel_cost, 2),
        "total_gallons": round(total_distance / mpg, 2)
    }