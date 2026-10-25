from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import osmnx as ox

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "graph" / "chennai_drive.graphml"
OUT = ROOT / "data" / "location" / "chennai_streets.csv"


def midpoint_from_edge(row, u, v, G):
    geom = row.get("geometry")
    if geom is not None and hasattr(geom, "centroid"):
        p = geom.centroid
        return float(p.y), float(p.x)
    a = G.nodes[u]
    b = G.nodes[v]
    return ((float(a["y"]) + float(b["y"])) / 2.0, (float(a["x"]) + float(b["x"])) / 2.0)


def main() -> None:
    if not GRAPH.exists():
        raise FileNotFoundError(f"Missing graph: {GRAPH}")

    G = ox.load_graphml(GRAPH)
    points: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for u, v, _, data in G.edges(keys=True, data=True):
        name = data.get("name")
        if isinstance(name, (list, tuple)):
            names = [str(x).strip() for x in name if str(x).strip()]
        else:
            names = [str(name).strip()] if name else []
        for street in names:
            if street:
                points[street].append(midpoint_from_edge(data, u, v, G))

    rows = []
    for name, coords in sorted(points.items(), key=lambda x: x[0].lower()):
        lat = sum(p[0] for p in coords) / len(coords)
        lon = sum(p[1] for p in coords) / len(coords)
        rows.append({
            "name": name,
            "normalized_name": " ".join(ch.lower() if ch.isalnum() else " " for ch in name).split() and " ".join(ch.lower() if ch.isalnum() else " " for ch in name).split(),
            "source": "OpenStreetMap road graph",
            "latitude": f"{lat:.7f}",
            "longitude": f"{lon:.7f}",
            "segment_count": str(len(coords)),
        })

    # Fix normalized_name creation without locale-specific dependencies.
    for r in rows:
        r["normalized_name"] = " ".join("".join(c.lower() if c.isalnum() else " " for c in r["name"]).split())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows):,} Chennai street names with representative coordinates to {OUT}")


if __name__ == "__main__":
    main()
