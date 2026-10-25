# Chennai EV Trip Planner — Navigation Foundation v1

This package implements the next stage requested for the final-year EV project:

- full-screen map-first React UI
- browser current-location GPS
- submitted exact-address/landmark search inside Chennai District
- click-on-map destination selection
- Chennai District road graph from OpenStreetMap
- local Dijkstra shortest-path routing
- multiple route candidates using OSMnx k-shortest paths
- user route selection by clicking the route or route card
- MongoDB vehicle selector

## Why this is separate from the current Streamlit app

The current Streamlit page is a working AI/charging prototype, but it cannot give the desired navigation-app interaction cleanly. This frontend replaces only the UI/routing shell first. The existing XGBoost/SOC/PuLP modules will be connected after this foundation is verified.

## 1. Backend

From `D:\EV_TripPlanner` (after copying these folders into the project):

```powershell
python -m pip install -r requirements-navigation.txt
```

Make sure MongoDB is running locally.

Then build the real Chennai road graph once:

```powershell
python scripts/build_chennai_network.py
```

This creates:

```text
data/boundary/chennai_district.geojson
data/graph/chennai_drive.graphml
```

OSMnx supports downloading a driving graph from a polygon and provides nearest-node and shortest-path routing. The saved graph lets runtime routing happen locally instead of asking OSRM for every user route. Cite OpenStreetMap/OSMnx appropriately in the report.

Start the API:

```powershell
uvicorn api.main:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## 3. First test

1. Click `◎ Use my current location`.
2. Search a real Chennai address/landmark and press Enter.
3. Click a returned address, or click directly on the map.
4. Click `Plan route`.
5. Route alternatives should appear at the bottom-left.
6. Click a route line or route card to select it.
7. Select the EV model and SOC in the right panel.

## Important data/service notes

The address search uses a submitted-query Nominatim request, not keystroke autocomplete. The public Nominatim service has a 1 request/second maximum and requires an identifying User-Agent/Referer, so this code deliberately throttles requests and searches only on submission.

The map uses OpenFreeMap's MapLibre Liberty style. OpenFreeMap documents this style URL and provides the map service without an API key.

The primary route uses Dijkstra weighted by graph travel time. OSMnx documents its shortest-path routing as Dijkstra-based. Multiple alternatives use OSMnx's k-shortest path implementation. This gives the project a defensible distinction between the primary Dijkstra route and alternative route generation.

## What is NOT connected yet

The following existing project modules are intentionally NOT rewritten in this v1 package:

- XGBoost energy prediction
- 25% SOC feasibility calculation
- charging-station filtering
- PuLP/MILP optimization
- live trip SOC monitoring
- charging alerts

Once the navigation foundation works, these should be connected to the selected route.
