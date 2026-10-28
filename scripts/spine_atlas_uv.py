#!/usr/bin/env python3
"""Spine 4.2 atlas UV adapter.

Spine JSON mesh `uvs` are normalized INSIDE an attachment's region, not
the entire atlas image. This adapter maps them into normalized page UVs,
including 90/180/270 degree atlas rotation and whitespace trim offsets.

Formulas independently implemented against the official Spine 4.2
MeshAttachment.updateRegion / TextureAtlas semantics. Do not silently
fallback to region-local UVs when atlas lookup fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class AtlasRegion:
    name: str
    page: str
    page_width: int
    page_height: int
    x: int
    y: int
    width: int
    height: int
    degrees: int
    offset_x: int
    offset_y: int
    original_width: int
    original_height: int


def parse_atlas(source: str) -> dict[str, AtlasRegion]:
    lines = source.replace("\r\n", "\n").split("\n")
    regions: dict[str, AtlasRegion] = {}
    page_name = None
    page_data = {}
    region_name = None
    region_data = {}
    after_gap = True

    def fields(raw: dict, required: str, size: int) -> tuple[int, ...]:
        value = raw.get(required)
        if value is None:
            raise ValueError(f"Missing atlas {required}: {raw}")
        items = tuple(int(t.strip()) for t in value.split(","))
        if len(items) != size:
            raise ValueError(f"Invalid atlas field {required}: {value}")
        return items

    def flush_region():
        nonlocal region_name, region_data
        if region_name is None:
            return
        if not page_name:
            raise ValueError(f"Atlas region without page: {region_name}")
        pw, ph = fields(page_data, "size", 2)
        x, y, w, h = fields(region_data, "bounds", 4)
        offs = fields(region_data, "offsets", 4) if "offsets" in region_data else (0, 0, w, h)
        rotation = region_data.get("rotate", "false")
        degrees = 90 if rotation == "true" else (0 if rotation == "false" else int(rotation))
        if degrees not in (0, 90, 180, 270):
            raise ValueError(f"Unsupported atlas rotation: {degrees}")
        if region_name in regions:
            raise ValueError(f"Duplicate atlas name: {region_name}")
        if min(pw, ph, w, h, offs[2], offs[3]) <= 0:
            raise ValueError(f"Invalid atlas size: {region_name}")
        regions[region_name] = AtlasRegion(
            region_name, page_name, pw, ph, x, y, w, h, degrees,
            offs[0], offs[1], offs[2], offs[3])
        region_name, region_data = None, {}

    for original in lines + [""]:
        line = original.strip()
        if not line:
            flush_region()
            after_gap = True
            continue
        if ":" not in line:
            if after_gap or page_name is None:
                flush_region()
                page_name = line
                page_data = {}
            else:
                flush_region()
                region_name = line
                region_data = {}
            after_gap = False
            continue
        key, value = line.split(":", 1)
        if region_name is None:
            if page_name is None:
                # Optional atlas header before page title.
                continue
            page_data[key.strip()] = value.strip()
        else:
            region_data[key.strip()] = value.strip()
        after_gap = False

    if not regions:
        raise ValueError("No valid atlas regions")
    return regions


def to_atlas_uv(region: AtlasRegion, u: float, v: float) -> tuple[float, float]:
    """Map mesh source region-relative UV to atlas page UV (Spine 4.2).

    Coordinates use the same top-left convention as Spine's 4.2 TS runtime.
    """
    if not (isfinite(u) and isfinite(v)):
        raise ValueError("Non-finite UV")
    w, h = region.page_width, region.page_height
    x, y, rw, rh = region.x, region.y, region.width, region.height
    ox, oy = region.offset_x, region.offset_y
    ow, oh = region.original_width, region.original_height

    if region.degrees == 90:
        x0 = x - (oh - oy - rh)
        y0 = y - (ow - ox - rw)
        atlas_x = x0 + v * oh
        atlas_y = y0 + (1 - u) * ow
    elif region.degrees == 180:
        atlas_x = x - (ow - ox - rw) + (1 - u) * ow
        atlas_y = y - oy + (1 - v) * oh
    elif region.degrees == 270:
        atlas_x = x - oy + (1 - v) * oh
        atlas_y = y - ox + u * ow
    else:
        atlas_x = x - ox + u * ow
        atlas_y = y - (oh - oy - rh) + v * oh
    result = (atlas_x / w, atlas_y / h)
    if any(not isfinite(i) for i in result):
        raise ValueError("Non-finite normalized atlas UV")
    return result


def convert_mesh_uvs(
    uvs: Iterable[tuple[float, float]], *, atlas: dict[str, AtlasRegion],
    attachment: dict, attachment_name: str, expected_page: str,
) -> tuple[list[tuple[float, float]], AtlasRegion]:
    region_name = attachment.get("path") or attachment_name
    if region_name not in atlas:
        raise KeyError(f"Source mesh atlas region absent: {region_name!r}")
    region = atlas[region_name]
    if region.page != expected_page:
        raise ValueError(f"Multi-page atlas not supported: {region.page} vs {expected_page}")
    result = [to_atlas_uv(region, u, v) for u, v in uvs]
    return result, region
