# Fuel Route Planner API

A Django REST API that calculates the optimal fuel stops along a driving route
within the USA, minimizing fuel costs based on real price data.

---

## How It Works

1. User provides a start and finish location within the USA
2. API fetches the driving route via OpenRouteService (one API call)
3. Algorithm places fuel stops every ~400 miles (vehicle max range = 500 miles)
4. At each stop, picks the **cheapest** nearby fuel station from our dataset
5. Returns total fuel cost assuming 10 miles per gallon

---

## Tech Stack

- Python 3.12
- Django 6.0.6
- Django REST Framework
- OpenRouteService API (free, for routing)
- OpenStreetMap (for map URL)

---

## Setup Instructions

### 1. Clone the repo

```
git clone (https://github.com/chinmayy13/fuel_route_planner)
cd fuel_route_project
```

### 2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a .env file in the root folder:
```
ORS_API_KEY=your_openrouteservice_api_key_here
```

Get a free API key at: https://openrouteservice.org/dev/#/signup

### 5. Run migrations
```
python manage.py migrate
```

### 6. Start the server
```
python manage.py runserver
```
---

## API Usage

### Endpoint
```
POST /api/route/
```

### Request Body
```
{
"start": "New York, NY",
"finish": "Los Angeles, CA"
}
```

### Response
```
{
"status": "success",
"route": {
"start": "New York, NY",
"finish": "Los Angeles, CA",
"distance_miles": 2797.3,
"duration_hours": 45.05,
"map_url": "https://www.openstreetmap.org/directions?..."
},
"vehicle_info": {
"max_range_miles": 500,
"fuel_efficiency_mpg": 10
},
"fuel_stops": [
{
"stop_number": 1,
"mile_marker": 400,
"city": "Baltimore",
"state": "Maryland",
"fuel_price_per_gallon": 3.48,
"gallons_to_fill": 40.0,
"cost_at_this_stop": 139.2,
"coordinates": { "lat": 39.2904, "lon": -76.6122 }
}
],
"summary": {
"total_stops": 6,
"total_gallons_needed": 279.73,
"total_fuel_cost_usd": 1039.17
}
}
```
---

## Project Structure
```
fuel_route_project/
├── fuel_route/ → Django project config
│ ├── settings.py → App settings + custom config
│ └── urls.py → Root URL routing
├── route_planner/ → Main app
│ ├── services/
│ │ ├── fuel.py → Loads CSV, finds nearby stations
│ │ ├── routing.py → Calls ORS API, samples waypoints
│ │ └── optimizer.py → Picks cheapest stops, calculates cost
│ ├── views.py → API endpoint logic
│ └── urls.py → App URL routing
├── fuel_prices.csv → Fuel price dataset by city/state
├── requirements.txt → Python dependencies
└── .env → Secret keys (not committed to git)
```
---

## Algorithm explanation

- Fuel stops are placed every 400 miles (not 500) as a safety buffer
- At each stop, all stations within 150 miles of the route are considered
- Stations are sorted by price — cheapest is always selected
- Cost = (miles for that leg ÷ 10 mpg) × price per gallon
- Final leg to destination is also accounted for

## Algorithm Design

### Fuel Stop Optimization — Greedy Approach

The fuel stop optimizer uses a **greedy algorithm**:

- The route is divided into segments every 400 miles (80% of 500 mile max range)
- At each segment, all fuel stations within 150 miles are considered
- The **cheapest station** at that point is always selected
- Cost = (miles for that leg ÷ 10 mpg) × price per gallon

**Why greedy?**
A globally optimal solution would look ahead — for example,
buying extra fuel at a $3.00 station before entering a region
where all stations charge $4.50. The greedy approach doesn't do this.

However, greedy works well in practice because:

- It runs in O(n) time — very fast
- Real fuel tanks have physical limits anyway
- Price differences across regions are rarely extreme enough
  to justify a more complex algorithm for this use case

**Example:**
New York → Los Angeles (2,797 miles)

- Stop every ~400 miles = 6 stops
- Algorithm picks cheapest nearby station at each stop
- Correctly identifies cheap Texas/Midwest stations
  and expensive California stations

## Known Limitations & Design Decisions

- **Fuel station coordinates** are approximated within state boundaries
  using a deterministic hash-based approach. This ensures every station
  gets unique coordinates instantly with zero API calls. Accuracy improves
  if exact GPS coordinates are available via geocoding.

- **Fuel optimization uses a greedy algorithm** — picks cheapest station
  at each stop. A globally optimal solution would look ahead and buy more
  fuel before expensive regions.

- **Map is returned as an OpenStreetMap URL** rather than an embedded map.

- **Only US locations are supported.** Non-US locations return a clear
  error message.

- **Multiple stops in same state are possible** on long routes — this is
  geographically correct (e.g. Texas spans ~800 miles east to west).

### Error Responses
```
Missing fields:
{
"error": "Both 'start' and 'finish' are required."
}

Non-USA location:
{
"error": "Only US locations are supported."
}
```
