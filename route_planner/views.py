from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .services.routing import get_route, sample_waypoints
from .services.optimizer import optimize_fuel_stops


class RoutePlannerView(APIView):
    """
    POST /api/route/

    Request body:
    {
        "start": "New York, NY",
        "finish": "Los Angeles, CA"
    }

    Response:
    {
        "status": "success",
        "cached": false,
        "route": { distance, duration, map_url },
        "fuel_stops": [...],
        "summary": { total_cost, total_gallons, ... }
    }
    """

    def post(self, request):

        start = request.data.get("start")
        finish = request.data.get("finish")

        if not start or not finish:
            return Response(
                {"error": "Both 'start' and 'finish' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = f"route_{start}_{finish}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)

        if cached_result:
            cached_result["cached"] = True
            return Response(cached_result, status=status.HTTP_200_OK)

        try:
            route_data = get_route(start, finish)

            waypoints = sample_waypoints(
                route_data["coordinates"],
                route_data["distance_miles"]
            )
            route_data["waypoints"] = waypoints

            fuel_plan = optimize_fuel_stops(route_data)

            start_lat, start_lon = route_data["start_coords"]
            finish_lat, finish_lon = route_data["finish_coords"]
            map_url = (
                f"https://www.openstreetmap.org/directions?"
                f"engine=fossgis_osrm_car&"
                f"route={start_lat},{start_lon};{finish_lat},{finish_lon}"
            )

            result = {
                "status": "success",
                "cached": False,
                "route": {
                    "start": start,
                    "finish": finish,
                    "distance_miles": route_data["distance_miles"],
                    "duration_hours": route_data["duration_hours"],
                    "map_url": map_url
                },
                "vehicle_info": {
                    "max_range_miles": 500,
                    "fuel_efficiency_mpg": 10
                },
                "fuel_stops": fuel_plan["fuel_stops"],
                "summary": {
                    "total_stops": len(fuel_plan["fuel_stops"]),
                    "total_gallons_needed": fuel_plan["total_gallons"],
                    "total_fuel_cost_usd": fuel_plan["total_fuel_cost"],
                    "optimization_strategy": "greedy - cheapest station at each stop"
                }
            }

            cache.set(cache_key, result, timeout=60 * 60 * 24)

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": f"Something went wrong: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )