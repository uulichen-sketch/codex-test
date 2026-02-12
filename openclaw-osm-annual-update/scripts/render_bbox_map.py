#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from common import append_log


def make_bbox_polygon(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat],
                ]
            ],
        },
        "properties": {"stroke": "#ff2d55", "stroke-width": 3, "fill": "#000000", "fill-opacity": 0},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render bbox overlay map via Mapbox Static API")
    parser.add_argument("--region-json", required=True)
    parser.add_argument("--out-png", required=True)
    parser.add_argument("--mapbox-token-env", default="MAPBOX_ACCESS_TOKEN")
    parser.add_argument("--mapbox-style", default="mapbox/streets-v12")
    parser.add_argument("--image-size", default="1000x700")
    args = parser.parse_args()

    region_path = Path(args.region_json)
    out_png = Path(args.out_png)
    log_path = out_png.parent.parent / "logs" / "run.log"

    with region_path.open("r", encoding="utf-8") as f:
        region = json.load(f)

    bbox = region["bbox"]["final"]
    min_lon, min_lat, max_lon, max_lat = [float(v) for v in bbox]

    token = os.getenv(args.mapbox_token_env)
    if not token:
        append_log(log_path, f"Mapbox token env missing: {args.mapbox_token_env}")
        print(json.dumps({"status": "skipped", "reason": "missing token env"}, ensure_ascii=False))
        return 0

    feature = make_bbox_polygon(min_lon, min_lat, max_lon, max_lat)
    encoded = urllib.parse.quote(json.dumps(feature, separators=(",", ":"), ensure_ascii=False), safe="")
    overlay = f"geojson({encoded})"

    static_url = (
        f"https://api.mapbox.com/styles/v1/{args.mapbox_style}/static/"
        f"{overlay}/[{min_lon},{min_lat},{max_lon},{max_lat}]/{args.image_size}"
        f"?access_token={token}"
    )

    out_png.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(static_url)
    with urllib.request.urlopen(req, timeout=60) as r:
        out_png.write_bytes(r.read())

    append_log(log_path, f"bbox map saved: {out_png}")
    print(json.dumps({"status": "ok", "out_png": str(out_png)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
