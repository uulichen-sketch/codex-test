from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def slugify_region(region_query: str) -> str:
    cleaned = re.sub(r"\s+", " ", region_query.strip())
    cleaned = re.sub(r"[^\w\-\s]", "", cleaned, flags=re.UNICODE)
    return cleaned.replace(" ", "_") or "region"


def ensure_output_tree(base_dir: Path) -> Dict[str, Path]:
    parts = {
        "meta": base_dir / "meta",
        "raw": base_dir / "raw",
        "download": base_dir / "raw" / "changeset_download",
        "stats": base_dir / "stats",
        "figures": base_dir / "figures",
        "logs": base_dir / "logs",
    }
    for p in parts.values():
        p.mkdir(parents=True, exist_ok=True)
    return parts


def geometry_bbox(geometry: Dict[str, Any]) -> Tuple[float, float, float, float]:
    coords: List[Tuple[float, float]] = []

    def walk(v: Any) -> None:
        if isinstance(v, list):
            if len(v) >= 2 and isinstance(v[0], (int, float)) and isinstance(v[1], (int, float)):
                coords.append((float(v[0]), float(v[1])))
            else:
                for i in v:
                    walk(i)

    walk(geometry.get("coordinates", []))
    if not coords:
        raise ValueError("No coordinates in geometry")
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))


def parse_bbox_list(values: Iterable[Any]) -> Tuple[float, float, float, float]:
    vals = list(values)
    if len(vals) != 4:
        raise ValueError("bbox must have 4 values")
    a, b, c, d = [float(x) for x in vals]
    # Nominatim search boundingbox is [south, north, west, east]
    if a <= b and c <= d:
        return (c, a, d, b)
    return (a, b, c, d)


def bbox_diff(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> Dict[str, float]:
    min_lon_diff = abs(a[0] - b[0])
    min_lat_diff = abs(a[1] - b[1])
    max_lon_diff = abs(a[2] - b[2])
    max_lat_diff = abs(a[3] - b[3])
    area_a = max((a[2] - a[0]) * (a[3] - a[1]), 0.0)
    area_b = max((b[2] - b[0]) * (b[3] - b[1]), 0.0)
    area_ratio = 0.0 if area_a == 0 else abs(area_a - area_b) / area_a
    return {
        "min_lon_diff": min_lon_diff,
        "min_lat_diff": min_lat_diff,
        "max_lon_diff": max_lon_diff,
        "max_lat_diff": max_lat_diff,
        "area_ratio_diff": area_ratio,
    }


def polygon_hash(geometry: Dict[str, Any]) -> str:
    raw = json.dumps(geometry, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(message.rstrip() + "\n")
