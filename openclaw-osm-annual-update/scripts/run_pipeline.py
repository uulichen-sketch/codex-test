#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from common import ensure_output_tree, slugify_region, write_json


def run_cmd(args: list[str]) -> None:
    proc = subprocess.run(args, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{proc.stderr}")
    if proc.stdout.strip():
        print(proc.stdout.strip())


def write_summary_stub(base_dir: Path, region_query: str, year: int, timezone: str, granularity: str) -> None:
    region_json_path = base_dir / "meta" / "region.json"
    region = {}
    if region_json_path.exists():
        region = json.loads(region_json_path.read_text(encoding="utf-8"))

    summary = {
        "meta": {
            "region_query": region_query,
            "year": year,
            "timezone": timezone,
            "granularity": granularity,
            "t_start": f"{year}-01-01T00:00:00Z",
            "t_end": f"{year + 1}-01-01T00:00:00Z",
            "chosen_osm_object": region.get("chosen_osm_object"),
            "boundary_source": (region.get("meta") or {}).get("boundary_source"),
            "bbox": (region.get("bbox") or {}).get("final"),
            "polygon_hash": region.get("polygon_hash"),
        },
        "changesets": {"CS_total": 0, "CHG_total": 0, "monthly": []},
        "contributors": {"U_total": 0, "AU_10cs": 0, "AU_500chg": 0, "topk_users_by_chg": []},
        "features": {"FEAT_EDIT_total": {}, "FEAT_EDIT_BY_TAG_total": {}, "UNIQUE_FEAT_total": None},
        "roads": {
            "ERL_raw_total": 0.0,
            "ERL_unique_total": 0.0,
            "monthly": [],
            "missing_nodes_rate": None,
            "affected_ways_count": 0,
            "method_note": "TBD: geodesic length from way node coordinates",
        },
        "quality": {
            "truncation_windows": [],
            "bbox_cross_border_risk_note": "changeset bbox hit may include cross-border edits",
            "api_errors": [],
            "retries": [],
            "partial_failures": [],
        },
    }
    write_json(base_dir / "stats" / "summary.json", summary)


def write_monthly_stub(base_dir: Path, year: int) -> None:
    path = base_dir / "stats" / "monthly.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "CS", "CHG", "U", "ERL_raw", "ERL_unique"])
        for m in range(1, 13):
            writer.writerow([f"{year}-{m:02d}", 0, 0, 0, 0, 0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap OSM annual update skill outputs")
    parser.add_argument("--region-query", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--out-dir", default="outputs")
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--granularity", default="month")
    parser.add_argument("--nominatim-base", default="https://nominatim.openstreetmap.org")
    parser.add_argument("--mapbox-token-env", default="MAPBOX_ACCESS_TOKEN")
    parser.add_argument("--mapbox-style", default="mapbox/streets-v12")
    parser.add_argument("--image-size", default="1000x700")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    region_slug = slugify_region(args.region_query)
    base_dir = Path(args.out_dir) / region_slug / str(args.year)
    ensure_output_tree(base_dir)

    (base_dir / "raw" / "changesets.csv").touch(exist_ok=True)
    (base_dir / "logs" / "run.log").touch(exist_ok=True)

    run_cmd(
        [
            sys.executable,
            str(root / "resolve_region.py"),
            "--region-query",
            args.region_query,
            "--year",
            str(args.year),
            "--out-dir",
            args.out_dir,
            "--timezone",
            args.timezone,
            "--nominatim-base",
            args.nominatim_base,
        ]
    )

    run_cmd(
        [
            sys.executable,
            str(root / "render_bbox_map.py"),
            "--region-json",
            str(base_dir / "meta" / "region.json"),
            "--out-png",
            str(base_dir / "figures" / "bbox_map.png"),
            "--mapbox-token-env",
            args.mapbox_token_env,
            "--mapbox-style",
            args.mapbox_style,
            "--image-size",
            args.image_size,
        ]
    )

    write_summary_stub(base_dir, args.region_query, args.year, args.timezone, args.granularity)
    write_monthly_stub(base_dir, args.year)

    print(
        json.dumps(
            {
                "status": "ok",
                "base_dir": str(base_dir),
                "generated_at": dt.datetime.utcnow().isoformat() + "Z",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
