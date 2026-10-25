from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import osmnx as ox
from fastapi import APIRouter, HTTPException
from shapely.geometry import LineString
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "graph" / "chennai_drive.graphml"

router = APIRouter(prefix="/api/route", tags=["routing-diverse"])


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _edge_geometry(data: dict[str, Any], u_data: dict[str, Any], v_data: dict[str, Any]):
    geom = data.get("geometry")
    if isinstance(geom, LineString):
        return geom
    if isinstance(geom, str):
        try:
            parsed = wkt.loads(geom)
            if isinstance(parsed, LineString):
                return parsed
        except Exception:
            pass

    ux, uy = _float(u_data.get("x")), _float(u_data.get("y"))
    vx, vy = _float(v_data.get("x")), _float(v_data.get("y"))
    return LineString([(ux, uy), (vx, vy)])


@lru_cache(maxsize=1)
def load_graph() -> tuple[nx.MultiDiGraph, nx.DiGraph]:
    if not GRAPH_PATH.exists():
        raise RuntimeError(f"Chennai road graph not found: {GRAPH_PATH}")

    raw = ox.load_graphml(GRAPH_PATH)
    if not isinstance(raw, (nx.MultiDiGraph, nx.MultiGraph, nx.DiGraph)):
        raise RuntimeError("Unsupported Chennai road graph type.")

    if not raw.is_directed():
        raw = raw.to_directed()

    # Keep only the lowest-travel-time parallel edge for each directed pair.
    # The original edge geometry is retained so the returned route follows the
    # real OSM road shape rather than simply drawing straight node-to-node lines.
    compact = nx.DiGraph()
    for u, v, key, data in raw.edges(keys=True, data=True):
        base_time = _float(data.get("travel_time"), _float(data.get("length"), 1.0))
        length = _float(data.get("length"), 0.0)
        payload = {
            "base_time": max(base_time, 1e-6),
            "length": max(length, 0.0),
            "geometry": _edge_geometry(data, raw.nodes[u], raw.nodes[v]),
            "key": key,
        }
        if not compact.has_edge(u, v) or payload["base_time"] < compact[u][v]["base_time"]:
            compact.add_edge(u, v, **payload)

    return raw, compact


def _nearest_node(graph: nx.MultiDiGraph, lat: float, lon: float):
    node, _ = ox.nearest_nodes(graph, X=lon, Y=lat, return_dist=True)
    n = graph.nodes[node]
    nlat = _float(n.get("y"))
    nlon = _float(n.get("x"))
    return node, nlat, nlon


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(h)))


def _path_edges(path: list[Any]):
    return list(zip(path[:-1], path[1:]))


def _path_stats(graph: nx.DiGraph, path: list[Any]) -> tuple[float, float]:
    distance_km = 0.0
    duration_min = 0.0
    for u, v in _path_edges(path):
        e = graph[u][v]
        distance_km += _float(e.get("length")) / 1000.0
        duration_min += _float(e.get("base_time")) / 60.0
    return distance_km, duration_min


def _path_overlap(a: list[Any], b: list[Any]) -> float:
    ea = set(_path_edges(a))
    eb = set(_path_edges(b))
    if not ea or not eb:
        return 0.0
    return len(ea & eb) / max(1, min(len(ea), len(eb)))


def _path_geometry(raw_graph: nx.MultiDiGraph, compact: nx.DiGraph, path: list[Any]):
    coords: list[list[float]] = []

    for u, v in _path_edges(path):
        edge = compact[u][v]
        geom = edge.get("geometry")
        if not isinstance(geom, LineString):
            ux, uy = _float(raw_graph.nodes[u].get("x")), _float(raw_graph.nodes[u].get("y"))
            vx, vy = _float(raw_graph.nodes[v].get("x")), _float(raw_graph.nodes[v].get("y"))
            part = [(ux, uy), (vx, vy)]
        else:
            part = list(geom.coords)
            if len(part) >= 2:
                ux = _float(raw_graph.nodes[u].get("x"))
                uy = _float(raw_graph.nodes[u].get("y"))
                d_first = _haversine_m(uy, ux, float(part[0][1]), float(part[0][0]))
                d_last = _haversine_m(uy, ux, float(part[-1][1]), float(part[-1][0]))
                if d_last < d_first:
                    part.reverse()

        for x, y in part:
            xy = [float(x), float(y)]
            if not coords or abs(coords[-1][0] - xy[0]) > 1e-10 or abs(coords[-1][1] - xy[1]) > 1e-10:
                coords.append(xy)

    if len(coords) < 2:
        for node in path:
            coords.append([_float(raw_graph.nodes[node].get("x")), _float(raw_graph.nodes[node].get("y"))])

    return {"type": "LineString", "coordinates": coords}


def _dijkstra(compact: nx.DiGraph, source: Any, target: Any, penalties: dict[tuple[Any, Any], float]):
    def weight(u, v, data):
        return data["base_time"] * penalties.get((u, v), 1.0)

    return nx.dijkstra_path(compact, source, target, weight=weight)


def _diverse_paths(compact: nx.DiGraph, source: Any, target: Any, count: int) -> list[list[Any]]:
    primary = _dijkstra(compact, source, target, {})
    paths = [primary]
    if count <= 1:
        return paths

    penalties: dict[tuple[Any, Any], float] = {}

    # Repeatedly penalise already-used edges. This keeps Dijkstra as the route
    # algorithm while forcing subsequent alternatives onto other road segments.
    for _ in range(1, count):
        for u, v in _path_edges(paths[-1]):
            penalties[(u, v)] = penalties.get((u, v), 1.0) * 6.0

        candidate = None
        for multiplier in (1.0, 2.0, 4.0, 8.0):
            trial = dict(penalties)
            if multiplier != 1.0:
                trial = {edge: value * multiplier for edge, value in trial.items()}
            try:
                trial_path = _dijkstra(compact, source, target, trial)
            except nx.NetworkXNoPath:
                continue
            if any(trial_path == p for p in paths):
                continue
            if max((_path_overlap(trial_path, old) for old in paths), default=0.0) <= 0.80:
                candidate = trial_path
                break
            if candidate is None:
                candidate = trial_path

        if candidate is None:
            break
        paths.append(candidate)

    return paths


@router.post("/diverse")
def diverse_route(payload: dict[str, Any]):
    try:
        origin = payload.get("origin") or {}
        destination = payload.get("destination") or {}
        lat1, lon1 = _float(origin.get("lat")), _float(origin.get("lon"))
        lat2, lon2 = _float(destination.get("lat")), _float(destination.get("lon"))
        requested = max(1, min(3, int(payload.get("alternatives", 3))))

        raw, compact = load_graph()
        source, slat, slon = _nearest_node(raw, lat1, lon1)
        target, tlat, tlon = _nearest_node(raw, lat2, lon2)
        if source == target:
            raise HTTPException(status_code=400, detail="Origin and destination snap to the same road node.")

        paths = _diverse_paths(compact, source, target, requested)
        routes = []
        for idx, path in enumerate(paths):
            distance_km, duration_min = _path_stats(compact, path)
            routes.append({
                "route_id": idx,
                "distance_km": round(distance_km, 2),
                "duration_min": round(duration_min, 1),
                "geometry": _path_geometry(raw, compact, path),
            })

        return {
            "origin": {"lat": lat1, "lon": lon1},
            "destination": {"lat": lat2, "lon": lon2},
            "routes": routes,
            "count": len(routes),
            "algorithm": "Dijkstra + edge-penalized diverse alternatives",
            "scope": "Chennai District",
            "snapping": {
                "origin_snap_m": round(_haversine_m(lat1, lon1, slat, slon), 1),
                "destination_snap_m": round(_haversine_m(lat2, lon2, tlat, tlon), 1),
                "primary_algorithm": "Dijkstra",
                "alternatives_algorithm": "Dijkstra with route-edge penalties",
            },
        }
    except HTTPException:
        raise
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=400, detail="No drivable Chennai road path was found between these points.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Diverse route calculation failed: {exc}")


def register_diverse_routes(app):
    app.include_router(router)
