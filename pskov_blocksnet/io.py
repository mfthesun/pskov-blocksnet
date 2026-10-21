"""Чтение и запись GeoJSON в едином формате (EPSG:4326, UTF-8, округление координат)."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from loguru import logger


def write_geojson(gdf: gpd.GeoDataFrame, path: Path, precision: int = 6) -> Path:
    """Сохраняет слой в GeoJSON (WGS84). 6 знаков после запятой ≈ 10 см — достаточно и экономит место."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf = gdf.to_crs(4326) if gdf.crs is not None else gdf.set_crs(4326)
    for col in gdf.columns:
        if col != gdf.geometry.name and gdf[col].dtype == object:
            gdf[col] = gdf[col].astype("string")
    if path.exists():
        path.unlink()
    gdf.to_file(path, driver="GeoJSON", engine="pyogrio", layer_options={"COORDINATE_PRECISION": precision,
                                                                         "RFC7946": "YES"})
    logger.info(f"Сохранено: {path.relative_to(path.parents[2]) if len(path.parents) > 2 else path} ({len(gdf)})")
    return path


def read_geojson(path: Path, crs: int | None = None) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path, engine="pyogrio")
    return gdf.to_crs(crs) if crs else gdf
