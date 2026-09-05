#!/usr/bin/env python3
"""Sample a Wavefront OBJ mesh into a point cloud for the constellation engine.

The `points` source in assets/js/constellation.js draws any list of 3D points
as stars. This turns a mesh into that list by sampling its surface uniformly
by area, so a model exported from Blender, FreeCAD or a CAD tool can be a
scene in _data/constellations/ with `url: /assets/data/constellations/x.json`.

Design constraints:
  - Standard library only. Triangles and polygons (fan-triangulated) are read
    from `v` and `f` records; normals, textures, groups and materials are
    ignored, which is all a point cloud needs.
  - Deterministic: a fixed seed, so the same mesh gives the same file.
  - Output is normalized to a unit half-size and centered, matching what the
    engine does for inline points, and written compactly (3 decimals).

Usage:
  python3 scripts/sample_mesh_points.py model.obj -o assets/data/constellations/model.json
  python3 scripts/sample_mesh_points.py model.obj --count 2400 --seed 7 > model.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path


def read_obj(path: Path) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v" and len(parts) >= 4:
            verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "f" and len(parts) >= 4:
            idx = []
            for token in parts[1:]:
                i = int(token.split("/")[0])
                idx.append(i - 1 if i > 0 else len(verts) + i)
            for k in range(1, len(idx) - 1):          # fan triangulation
                tris.append((idx[0], idx[k], idx[k + 1]))
    return verts, tris


def tri_area(a, b, c) -> float:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def sample(verts, tris, count: int, seed: int) -> list[list[float]]:
    rng = random.Random(seed)
    areas = [tri_area(verts[a], verts[b], verts[c]) for a, b, c in tris]
    total = sum(areas)
    if total <= 0:
        raise SystemExit("mesh has no area to sample")
    # cumulative distribution over triangle area, then uniform barycentric points
    cumulative, acc = [], 0.0
    for area in areas:
        acc += area
        cumulative.append(acc)
    points = []
    for _ in range(count):
        r = rng.random() * total
        lo, hi = 0, len(cumulative) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        a, b, c = (verts[i] for i in tris[lo])
        u, v = rng.random(), rng.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        points.append([a[k] + u * (b[k] - a[k]) + v * (c[k] - a[k]) for k in range(3)])
    return points


def normalize(points: list[list[float]]) -> list[list[float]]:
    lo = [min(p[k] for p in points) for k in range(3)]
    hi = [max(p[k] for p in points) for k in range(3)]
    centre = [(lo[k] + hi[k]) / 2 for k in range(3)]
    radius = max(hi[k] - lo[k] for k in range(3)) / 2 or 1.0
    return [[round((p[k] - centre[k]) / radius, 3) for k in range(3)] for p in points]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("obj", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="write JSON here (default: stdout)")
    ap.add_argument("--count", type=int, default=2000, help="points to sample (default 2000)")
    ap.add_argument("--seed", type=int, default=20260905)
    args = ap.parse_args()

    verts, tris = read_obj(args.obj)
    if not tris:
        raise SystemExit(f"{args.obj}: no faces found")
    cloud = normalize(sample(verts, tris, args.count, args.seed))
    payload = {"source": args.obj.name, "count": len(cloud), "points": cloud}
    text = json.dumps(payload, separators=(",", ":")) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote {args.output} ({len(cloud)} points from {len(tris)} triangles)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
