from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_DIR = ROOT / "data" / "boundary"
GRAPH_DIR = ROOT / "data" / "graph"
BOUNDARY_PATH = BOUNDARY_DIR / "chennai_district.geojson"
GRAPH_PATH = GRAPH_DIR / "chennai_drive.graphml"


def main() -> None:
    BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    print("1/3  Looking up Chennai District boundary in OpenStreetMap...")
    gdf = ox.geocode_to_gdf("Chennai District, Tamil Nadu, India")
    if gdf.empty:
        raise RuntimeError("Could not find a Chennai District polygon in OSM.")

    # Select a polygonal result and dissolve multipart geometry if necessary.
    gdf = gdf[gdf.geometry.notna()].copy().to_crs(4326)
    polygon = gdf.geometry.union_all()
    boundary = gpd.GeoDataFrame(
        {"name": ["Chennai District"]},
        geometry=[polygon],
        crs="EPSG:4326",
    )
    boundary.to_file(BOUNDARY_PATH, driver="GeoJSON")
    print(f"    Saved boundary: {BOUNDARY_PATH}")

    print("2/3  Downloading drivable Chennai District road network...")
    graph = ox.graph_from_polygon(
        polygon,
        network_type="drive",
        simplify=True,
        retain_all=False,
        truncate_by_edge=True,
    )

    print("3/3  Adding travel-time weights and saving graph...")
    graph = ox.routing.add_edge_speeds(
        graph,
        hwy_speeds={
            "motorway": 70,
            "trunk": 60,
            "primary": 50,
            "secondary": 40,
            "tertiary": 35,
            "residential": 30,
            "unclassified": 30,
            "service": 20,
        },
        fallback=30,
        agg=np.median,
    )
    graph = ox.routing.add_edge_travel_times(graph)
    ox.save_graphml(graph, GRAPH_PATH)

    print(f"    Saved graph: {GRAPH_PATH}")
    print(f"    Nodes: {len(graph.nodes):,}")
    print(f"    Edges: {len(graph.edges):,}")
    print("DONE. The API can now run Dijkstra locally without asking OSRM for every route.")


if __name__ == "__main__":
    main()
