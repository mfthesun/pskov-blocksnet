"""Шаг 0. Подготовка входных данных по г. Пскову из материалов проекта PSKOKN.

Что делает:
  1. Граница городского округа Псков -> data/input/boundary.geojson
  2. Слои OSM из pskov_oblast.pbf (дороги, ж/д, вода, landuse, здания, школы) -> data/osm/*.geojson
  3. ОКН и зоны охраны — материалы по обоснованию СТП Псковской области 2025 г. (подготовка: Денис Яковлев) -> data/input/heritage_*.geojson
  4. Остановки общественного транспорта (подготовка: Виктор Цыганов) -> data/input/transport_stops.geojson
  5. Вырезка OSM по Пскову для пешеходного графа -> data/osm/pskov_city.osm.pbf (нужен osmium-tool)

Запуск (из корня репозитория, с активированным .venv):
    python scripts/prepare_data.py --source "<папка PSKOKN>" [--pbf <путь к pskov_oblast.pbf>]

Скрипт нужен один раз: его результаты уже лежат в репозитории. Повторять — только если
обновились исходники (новая выгрузка OSM, новая версия реестра ОКН).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pskov_blocksnet import config  # noqa: E402
from pskov_blocksnet.io import write_geojson  # noqa: E402
from pskov_blocksnet.osm_pbf import extract_layers  # noqa: E402

DEFAULT_SOURCE = Path.home() / "Claude" / "ИИ, анализ данных и моделирование в урбанистике" / "PSKOKN"

# Школы: в OSM под amenity=school попадают и не общеобразовательные учреждения.
NOT_GENERAL_SCHOOL = r"футбол|спорт|кибер|внешкольн|музык|художеств|автошкол|танц|искусств"


def load_boundary(source: Path) -> gpd.GeoDataFrame:
    path = source / "boundaries" / "городской округ Псков.gpkg"
    gdf = gpd.read_file(path).to_crs(4326)
    gdf = gdf[["name", "population", "wikidata", "geometry"]].copy()
    gdf["name"] = config.TERRITORY_NAME
    return gdf


def clean_schools(schools: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Точки школ: замкнутые линии -> полигоны -> точки, дубликаты и не-школы убираем."""
    from shapely.geometry import Polygon

    gdf = schools.copy()
    gdf["geometry"] = gdf.geometry.apply(
        lambda g: Polygon(g.coords) if g.geom_type == "LineString" and g.is_closed and len(g.coords) >= 4 else g
    )
    name = gdf["name"].fillna("")
    excluded = name.str.contains(NOT_GENERAL_SCHOOL, case=False, regex=True)
    logger.info(f"Школы: исключено как не общеобразовательные — {excluded.sum()}: {list(name[excluded])}")
    gdf = gdf[~excluded].copy()

    areas = gdf[gdf.geom_type.isin(["Polygon", "MultiPolygon"])]
    points = gdf[gdf.geom_type == "Point"]
    # точка внутри полигона школы — это тот же объект
    dup = points.sjoin(areas[["geometry"]], predicate="within", how="inner").index.unique()
    points = points.drop(index=dup)
    out = pd.concat([areas, points, gdf[~gdf.geom_type.isin(["Polygon", "MultiPolygon", "Point"])]])
    local = out.to_crs(config.LOCAL_CRS)
    out = out.set_geometry(local.representative_point().to_crs(4326))
    out["capacity"] = pd.to_numeric(out["capacity"], errors="coerce")
    return out.reset_index(drop=True)


def load_heritage(source: Path, boundary: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    path = source / "данные и материалы" / "OKN_Pskov_Region.gpkg"
    poly = boundary.union_all()
    out = {}
    columns = {
        "Heritage_Points": ["NAME", "ADDRESS", "REG_NUMBER", "HIST_CAT", "HER_TYPE", "Category", "semantic_type",
                            "UNESCO", "Особо_ценные", "STATUS"],
        "Heritage_Polygons": ["NAME", "ADDRESS", "NUMBER", "HIST_CAT", "Category", "semantic_type", "UNESCO",
                              "Особо_ценные", "STATUS"],
        "Protection_Zones": ["ZONE_DESC", "OBJECTNAME", "STATUS", "REESTRZOIT"],
    }
    names = {"Heritage_Points": "heritage_points", "Heritage_Polygons": "heritage_polygons",
             "Protection_Zones": "heritage_protection_zones"}
    for layer, cols in columns.items():
        gdf = gpd.read_file(path, layer=layer).to_crs(4326)
        gdf = gdf[gdf.intersects(poly)].copy()
        if layer != "Heritage_Points":
            gdf["geometry"] = gdf.geometry.make_valid().intersection(poly)
            gdf = gdf[~gdf.is_empty]
        out[names[layer]] = gdf[[c for c in cols if c in gdf.columns] + ["geometry"]].reset_index(drop=True)
        logger.info(f"{layer}: в границах Пскова — {len(out[names[layer]])}")
    return out


def load_transport(source: Path, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    path = source / "данные и материалы" / "transport_data.gpkg"
    poly = boundary.union_all()
    parts = []
    osm = gpd.read_file(path, layer="highway_bus_stop_osm").to_crs(4326)
    osm = osm[osm.within(poly)]
    parts.append(gpd.GeoDataFrame({"name": osm.get("name:ru", osm.get("name")), "kind": "bus_stop",
                                   "source": "OSM (highway=bus_stop)"}, geometry=osm.geometry))
    ya = gpd.read_file(path, layer="bus_stops_yandex").to_crs(4326)
    ya = ya[ya.within(poly)]
    parts.append(gpd.GeoDataFrame({"name": ya["name"], "kind": ya["transport_type"].fillna("bus"),
                                   "source": "Яндекс.Расписания"}, geometry=ya.geometry))
    rail = gpd.read_file(path, layer="train_platform_and_stations").to_crs(4326)
    rail = rail[rail.within(poly)]
    parts.append(gpd.GeoDataFrame({"name": rail.get("name"), "kind": "railway_" + rail["railway"].fillna(""),
                                   "source": "OSM (railway)"}, geometry=rail.geometry))
    stops = pd.concat(parts, ignore_index=True)
    stops["prepared_by"] = config.DATA_AUTHORS["transport"]
    logger.info(f"Остановки и станции в границах Пскова — {len(stops)} ({stops.source.value_counts().to_dict()})")
    return stops


def extract_city_pbf(pbf: Path, boundary: gpd.GeoDataFrame, buffer_m: float = 1500) -> None:
    """Вырезка PBF по границе города с буфером (граф строится с буфером 1 км) через osmium-tool."""
    import shutil
    import subprocess
    import tempfile

    if shutil.which("osmium") is None:
        logger.warning("osmium-tool не найден (sudo apt install osmium-tool) — вырезка PBF пропущена")
        return
    area = boundary.to_crs(config.LOCAL_CRS).buffer(buffer_m).to_crs(4326)
    with tempfile.TemporaryDirectory() as tmp:
        poly = Path(tmp) / "area.geojson"
        gpd.GeoDataFrame(geometry=area).to_file(poly, driver="GeoJSON")
        subprocess.run(["osmium", "extract", "-p", str(poly), "--strategy", "complete_ways", "--set-bounds",
                        "-O", "-o", str(config.CITY_PBF), str(pbf)], check=True)
    logger.info(f"Вырезка PBF: {config.CITY_PBF} ({config.CITY_PBF.stat().st_size / 1e6:.1f} МБ)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="папка PSKOKN с исходными данными")
    parser.add_argument("--pbf", type=Path, default=None, help="pskov_oblast.pbf (по умолчанию из --source)")
    args = parser.parse_args()
    pbf = args.pbf or args.source / "данные и материалы" / "pskov_oblast.pbf"

    boundary = load_boundary(args.source)
    write_geojson(boundary, config.INPUT_DIR / "boundary.geojson")

    for name, gdf in load_heritage(args.source, boundary).items():
        gdf["prepared_by"] = config.DATA_AUTHORS["heritage"]
        write_geojson(gdf, config.INPUT_DIR / f"{name}.geojson")

    write_geojson(load_transport(args.source, boundary), config.INPUT_DIR / "transport_stops.geojson")

    extract_city_pbf(pbf, boundary)
    layers = extract_layers(pbf, boundary)
    layers["schools"] = clean_schools(layers["schools"])
    for name, gdf in layers.items():
        write_geojson(gdf, config.OSM_DIR / f"{name}.geojson")
    logger.success("Данные подготовлены")


if __name__ == "__main__":
    main()
