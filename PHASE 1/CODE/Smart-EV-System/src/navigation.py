from __future__ import annotations

import json
from itertools import islice
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox
from shapely import wkt


class ChennaiRouter:
    """District-scoped road router using an OSM road graph.

    The graph is downloaded once and saved locally. Runtime routing is local:
    coordinates are snapped to the nearest road node, Dijkstra computes the
    shortest route, and OSMnx's k-shortest implementation supplies alternatives.
    """

    def __init__(self, graph_path: Path, boundary_path: Path):
        self.graph_path = Path(graph_path)
        self.boundary_path = Path(boundary_path)
        self._graph = None
        self._boundary = None

    @property
    def graph(self):
        if self._graph is None:
            if not self.graph_path.exists():
                raise FileNotFoundError(
                    f"Road graph not found: {self.graph_path}. "
                    "Run scripts/build_chennai_network.py first."
                )
            self._graph = ox.load_graphml(self.graph_path)
        return self._graph

    @property
    def boundary(self):
        if self._boundary is None:
            if not self.boundary_path.exists():
                raise FileNotFoundError(
                    f"District boundary not found: {self.boundary_path}. "
                    "Run scripts/build_chennai_network.py first."
                )
            import geopandas as gpd

            gdf = gpd.read_file(self.boundary_path).to_crs(4326)
            if gdf.empty:
                raise ValueError("Chennai district boundary file is empty.")
            self._boundary = gdf.geometry.union_all()
        return self._boundary

    def _snap(self, lat: float, lon: float) -> tuple[int, float]:
        node, distance = ox.distance.nearest_nodes(
            self.graph, X=float(lon), Y=float(lat), return_dist=True
        )
        return int(node), float(distance)

    @staticmethod
    def _edge_data(graph, u, v, key=None):
        data = graph.get_edge_data(u, v)
        if not data:
            raise KeyError(f"No edge found between {u} and {v}.")
        if graph.is_multigraph():
            if key is not None and key in data:
                return data[key]
            return min(data.values(), key=lambda d: float(d.get("length", 1e18)))
        return data

    def _path_to_geojson(self, path: list[int]) -> tuple[list[list[float]], float, float]:
        graph = self.graph
        coordinates: list[list[float]] = []
        total_length_m = 0.0
        total_time_s = 0.0

        for u, v in zip(path[:-1], path[1:]):
            edge = self._edge_data(graph, u, v)
            total_length_m += float(edge.get("length", 0.0) or 0.0)
            total_time_s += float(edge.get("travel_time", 0.0) or 0.0)

            geom = edge.get("geometry")
            if isinstance(geom, str):
                try:
                    geom = wkt.loads(geom)
                except Exception:
                    geom = None

            if geom is not None and hasattr(geom, "coords"):
                part = [[float(x), float(y)] for x, y in geom.coords]
                ux = float(graph.nodes[u]["x"])
                uy = float(graph.nodes[u]["y"])
                if part and abs(part[0][0] - ux) + abs(part[0][1] - uy) > abs(part[-1][0] - ux) + abs(part[-1][1] - uy):
                    part.reverse()
            else:
                part = [
                    [float(graph.nodes[u]["x"]), float(graph.nodes[u]["y"])],
                    [float(graph.nodes[v]["x"]), float(graph.nodes[v]["y"])],
                ]

            if coordinates:
                # Avoid duplicate join coordinate.
                coordinates.extend(part[1:])
            else:
                coordinates.extend(part)

        # A graph saved before travel_time was added should still work.
        if total_time_s <= 0:
            total_time_s = self._estimate_time_from_length(path)

        return coordinates, total_length_m / 1000.0, total_time_s / 60.0

    def _estimate_time_from_length(self, path: list[int]) -> float:
        """Fallback free-flow duration using a conservative local road speed."""
        total_m = 0.0
        for u, v in zip(path[:-1], path[1:]):
            edge = self._edge_data(self.graph, u, v)
            total_m += float(edge.get("length", 0.0) or 0.0)
        # 30 km/h fallback only if travel_time is missing in the graph.
        return (total_m / 1000.0) / 30.0 * 3600.0

    def _route_record(self, path: list[int], route_id: int, origin, destination, snap_meta):
        coords, distance_km, duration_min = self._path_to_geojson(path)
        return {
            "route_id": route_id,
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min, 1),
            "geometry": {
                "type": "LineString",
                "coordinates": coords,
            },
            "origin": {"lat": float(origin[0]), "lon": float(origin[1])},
            "destination": {"lat": float(destination[0]), "lon": float(destination[1])},
            "snapping": snap_meta,
        }

    def routes(self, origin: tuple[float, float], destination: tuple[float, float], k: int = 3) -> dict[str, Any]:
        """Return up to k route choices for (lat, lon) origin/destination."""
        k = max(1, min(int(k), 4))
        source, source_snap_m = self._snap(*origin)
        target, target_snap_m = self._snap(*destination)

        # Primary route: explicitly Dijkstra weighted by travel time.
        primary = ox.routing.shortest_path(
            self.graph, source, target, weight="travel_time", cpus=1
        )
        if primary is None:
            raise ValueError("No drivable route exists between the selected locations.")

        paths: list[list[int]] = [primary]

        if k > 1:
            # OSMnx implements Yen-style k-shortest paths on the road graph.
            for candidate in islice(
                ox.routing.k_shortest_paths(
                    self.graph, source, target, k=k, weight="travel_time"
                ),
                k,
            ):
                if candidate not in paths:
                    # Avoid nearly identical route options.
                    if len(candidate) < 2:
                        continue
                    paths.append(candidate)
                if len(paths) >= k:
                    break

        snap_meta = {
            "origin_snap_m": round(source_snap_m, 1),
            "destination_snap_m": round(target_snap_m, 1),
            "source_node": source,
            "destination_node": target,
            "routing_weight": "travel_time",
            "primary_algorithm": "Dijkstra",
            "alternatives_algorithm": "Yen-style k-shortest paths via OSMnx",
        }

        routes = [
            self._route_record(
                path, idx, origin, destination, snap_meta
            )
            for idx, path in enumerate(paths)
        ]

        # Guarantee stable ordering by travel time.
        routes.sort(key=lambda r: r["duration_min"])
        for idx, route in enumerate(routes):
            route["route_id"] = idx

        return {
            "routes": routes,
            "count": len(routes),
            "algorithm": "Dijkstra + k-shortest alternatives",
            "scope": "Chennai District",
        }


def write_geojson(geometry, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Chennai District"},
                "geometry": json.loads(geometry.to_json()),
            }
        ],
    }
    output_path.write_text(json.dumps(payload), encoding="utf-8")
