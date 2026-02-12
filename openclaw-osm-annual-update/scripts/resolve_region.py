#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

from common import append_log, bbox_diff, ensure_output_tree, geometry_bbox, parse_bbox_list, polygon_hash, slugify_region, write_json


def get_json(url: str, params: Dict[str, Any]) -> Any:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{qs}",
        headers={"User-Agent": "openclaw-osm-annual-update/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def select_candidate(candidates: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
    if not candidates:
        raise ValueError("No candidates returned by Nominatim")

    def score(c: Dict[str, Any]) -> Tuple[int, int]:
        cls = c.get("class") == "boundary"
        typ = c.get("type") == "administrative"
        return (1 if cls and typ else 0, int(c.get("place_rank") or 0))

    ranked = sorted(candidates, key=score, reverse=True)
    chosen = ranked[0]
    reason = "Prefer boundary+administrative, then higher place_rank"
    return chosen, reason


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve OSM administrative region + bbox")
    parser.add_argument("--region-query", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--nominatim-base", default="https://nominatim.openstreetmap.org")
    parser.add_argument("--bbox-diff-threshold", type=float, default=0.01)
    parser.add_argument("--bbox-area-ratio-threshold", type=float, default=0.05)
    args = parser.parse_args()

    region_slug = slugify_region(args.region_query)
    base_dir = Path(args.out_dir) / region_slug / str(args.year)
    dirs = ensure_output_tree(base_dir)
    log_path = dirs["logs"] / "run.log"

    append_log(log_path, f"[{dt.datetime.utcnow().isoformat()}Z] start resolve_region")

    search_url = f"{args.nominatim_base}/search"
    search_params = {"q": args.region_query, "format": "jsonv2", "addressdetails": 1, "limit": 5}
    candidates = get_json(search_url, search_params)
    chosen, reason = select_candidate(candidates)

    osm_type = str(chosen.get("osm_type", "")).upper()[:1]
    osm_id = int(chosen.get("osm_id"))
    lookup_url = f"{args.nominatim_base}/lookup"
    lookup_params = {"osm_ids": f"{osm_type}{osm_id}", "format": "geojson", "polygon_geojson": 1}
    payload = get_json(lookup_url, lookup_params)

    features = payload.get("features", [])
    if not features:
        raise ValueError("Lookup returned empty features")

    feat = features[0]
    geom = feat.get("geometry")
    if not geom:
        raise ValueError("Lookup feature missing geometry")

    bbox_from_geom = geometry_bbox(geom)
    bbox_lookup = None
    if "bbox" in feat:
        bbox_lookup = tuple(feat["bbox"])
    elif chosen.get("boundingbox"):
        bbox_lookup = parse_bbox_list(chosen["boundingbox"])

    final_bbox = bbox_from_geom
    diff = None
    source = "geometry_computed"
    if bbox_lookup:
        bbox_lookup = tuple(float(x) for x in bbox_lookup)
        diff = bbox_diff(bbox_from_geom, bbox_lookup)
        over_threshold = any(
            [
                diff["min_lon_diff"] > args.bbox_diff_threshold,
                diff["min_lat_diff"] > args.bbox_diff_threshold,
                diff["max_lon_diff"] > args.bbox_diff_threshold,
                diff["max_lat_diff"] > args.bbox_diff_threshold,
                diff["area_ratio_diff"] > args.bbox_area_ratio_threshold,
            ]
        )
        if not over_threshold:
            final_bbox = bbox_lookup
            source = "lookup_bbox"

    region_json = {
        "meta": {
            "region_query": args.region_query,
            "region_slug": region_slug,
            "year": args.year,
            "timezone": args.timezone,
            "boundary_source": "nominatim",
            "selection_reason": reason,
            "bbox_source": source,
            "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        },
        "nominatim": {
            "search_params": search_params,
            "candidate_count": len(candidates),
            "candidates_topN": candidates,
            "chosen": chosen,
            "lookup_params": lookup_params,
        },
        "chosen_osm_object": {"osm_type": osm_type, "osm_id": osm_id, "display_name": chosen.get("display_name")},
        "bbox": {
            "final": list(final_bbox),
            "lookup": list(bbox_lookup) if bbox_lookup else None,
            "geometry_computed": list(bbox_from_geom),
            "diff": diff,
            "thresholds": {"degree": args.bbox_diff_threshold, "area_ratio": args.bbox_area_ratio_threshold},
        },
        "geometry": geom,
        "polygon_hash": polygon_hash(geom),
    }

    write_json(dirs["meta"] / "region.json", region_json)
    append_log(log_path, f"[{dt.datetime.utcnow().isoformat()}Z] region.json written")
    print(json.dumps({"region_json": str(dirs['meta'] / 'region.json'), "bbox": list(final_bbox)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
