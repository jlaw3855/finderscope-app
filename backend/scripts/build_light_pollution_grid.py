#!/usr/bin/env python3
"""Downsample World Atlas 2015 GeoTIFF to a JSON grid for runtime lookup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_INPUT_HINT = (
    "World Atlas 2015 GeoTIFF from GFZ DOI 10.5880/GFZ.1.4.2016.001 "
    "(World_Atlas_2015.zip on datapub.gfz-potsdam.de)"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "light_pollution"
    / "world_atlas_grid.json"
)


def build_grid(
    input_path: Path,
    output_path: Path,
    *,
    resolution_deg: float = 0.1,
) -> Path:
    """Downsample atlas GeoTIFF to row-major JSON grid."""
    try:
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.transform import from_origin
        from rasterio.warp import reproject
    except ImportError as exc:  # pragma: no cover - dev-only script
        raise SystemExit(
            "Install build deps: pip install -r backend/scripts/requirements-build.txt"
        ) from exc

    if not input_path.is_file():
        raise FileNotFoundError(f"Atlas GeoTIFF not found: {input_path}")

    cols = round(360.0 / resolution_deg)
    rows = round(180.0 / resolution_deg)
    dst_transform = from_origin(-180.0, 90.0, resolution_deg, resolution_deg)
    dst_array = np.full((rows, cols), -1.0, dtype=np.float32)

    with rasterio.open(input_path) as src:
        src_nodata = src.nodata if src.nodata is not None else -9999.0
        reproject(
            source=rasterio.band(src, 1),
            destination=dst_array,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:4326",
            resampling=Resampling.average,
            src_nodata=src_nodata,
            dst_nodata=-1.0,
        )

    values: list[float] = []
    for row in range(rows - 1, -1, -1):
        for col in range(cols):
            value = float(dst_array[row, col])
            if value < 0:
                values.append(-1.0)
            else:
                values.append(round(value, 6))

    payload = {
        "source": "world_atlas_2015",
        "resolution_deg": resolution_deg,
        "west": -180.0,
        "south": -90.0,
        "rows": rows,
        "cols": cols,
        "nodata": -1,
        "values": values,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build World Atlas light pollution JSON grid from GeoTIFF."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help=f"Path to World Atlas 2015 GeoTIFF. {DEFAULT_INPUT_HINT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=0.1,
        help="Grid cell size in degrees (default: 0.1)",
    )
    args = parser.parse_args()

    if args.resolution <= 0 or args.resolution > 1:
        print("resolution must be between 0 and 1 degrees", file=sys.stderr)
        return 1

    try:
        output = build_grid(args.input, args.output, resolution_deg=args.resolution)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Wrote light pollution grid to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
