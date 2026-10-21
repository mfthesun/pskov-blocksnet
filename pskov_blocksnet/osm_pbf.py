"""Извлечение слоёв OpenStreetMap из локального PBF-файла (офлайн-аналог osmnx.features_from_polygon).

Зачем: pipeline.ipynb BlocksNet скачивает данные через Overpass API (osmnx). Это медленно,
иногда падает по лимитам и не воспроизводимо во времени. У нас уже есть выгрузка OSM по
Псковской области (pskov_oblast.pbf), поэтому все слои берём из неё и обрезаем по границе города.

Набор тегов совпадает с pipeline.ipynb (раздел 1.1 — bc_tags), чтобы результат был сопоставим.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd
from loguru import logger

# --- Теги из pipeline.ipynb ---------------------------------------------------

ROAD_HIGHWAYS = [
    "construction", "crossing", "living_street", "motorway", "motorway_link", "motorway_junction",
    "pedestrian", "primary", "primary_link", "raceway", "residential", "road", "secondary",
    "secondary_link", "services", "tertiary", "tertiary_link", "track", "trunk", "trunk_link",
    "turning_circle", "turning_loop", "unclassified",
]
WATER_FILTER = {
    "natural": ["water", "bay"],
    "waterway": ["river", "canal", "ditch", "riverbank", "dock"],
    "landuse": ["basin", "reservoir"],
    "water": ["lake", "pond", "reservoir", "basin", "canal", "river"],
}

LINE_TYPES = ["LineString", "MultiLineString"]
AREA_TYPES = ["Polygon", "MultiPolygon"]


def _osm(pbf_path: Path, boundary: gpd.GeoDataFrame):
    from pyrosm import OSM

    polygon = boundary.to_crs(4326).union_all()
    return OSM(str(pbf_path), bounding_box=polygon), polygon


def _clip(gdf: gpd.GeoDataFrame | None, polygon, geom_types: list[str] | None = None) -> gpd.GeoDataFrame:
    if gdf is None or len(gdf) == 0:
        return gpd.GeoDataFrame(geometry=[], crs=4326)
    gdf = gdf.set_crs(4326, allow_override=True)
    gdf = gdf[gdf.geometry.notna() & gdf.intersects(polygon)].copy()
    if geom_types:
        gdf = gdf[gdf.geom_type.isin(geom_types)].copy()
    return gdf.reset_index(drop=True)


def extract_layers(pbf_path: Path, boundary: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    """Возвращает словарь слоёв в EPSG:4326: roads, railways, water, landuse, buildings, schools."""
    osm, polygon = _osm(pbf_path, boundary)
    layers: dict[str, gpd.GeoDataFrame] = {}

    logger.info("Дороги (highway из pipeline.ipynb)")
    roads = osm.get_data_by_custom_criteria(
        custom_filter={"highway": ROAD_HIGHWAYS}, filter_type="keep", keep_nodes=False, keep_relations=False
    )
    layers["roads"] = _sel(_clip(roads, polygon, LINE_TYPES), ["highway", "name"])

    logger.info("Железные дороги (railway=rail)")
    rail = osm.get_data_by_custom_criteria(
        custom_filter={"railway": ["rail"]}, filter_type="keep", keep_nodes=False, keep_relations=False
    )
    layers["railways"] = _sel(_clip(rail, polygon, LINE_TYPES), ["railway"])

    logger.info("Водные объекты")
    water = osm.get_data_by_custom_criteria(custom_filter=WATER_FILTER, filter_type="keep", keep_nodes=False)
    water = _clip(water, polygon, AREA_TYPES + LINE_TYPES)
    layers["water"] = _sel(water, ["natural", "waterway", "water", "landuse", "name"])

    logger.info("Функциональные зоны (landuse=*)")
    landuse = osm.get_landuse()
    landuse = _clip(landuse, polygon, AREA_TYPES)
    layers["landuse"] = _sel(landuse, ["landuse"]).dropna(subset=["landuse"])

    logger.info("Здания (building=*)")
    buildings = osm.get_buildings()
    buildings = _clip(buildings, polygon, AREA_TYPES)
    if "building:levels" not in buildings.columns and "tags" in buildings.columns:
        buildings["building:levels"] = buildings["tags"].apply(_tag("building:levels"))
    layers["buildings"] = _sel(buildings, ["building", "building:levels", "name", "addr:street",
                                           "addr:housenumber", "start_date"])

    logger.info("Школы (amenity=school)")
    schools = osm.get_data_by_custom_criteria(custom_filter={"amenity": ["school"]}, filter_type="keep")
    schools = _clip(schools, polygon)
    if "capacity" not in schools.columns:
        schools["capacity"] = schools["tags"].apply(_tag("capacity")) if "tags" in schools else None
    layers["schools"] = _sel(schools, ["amenity", "name", "capacity"])

    return layers


def _sel(gdf: gpd.GeoDataFrame, columns: list[str]) -> gpd.GeoDataFrame:
    """Оставляет osm_id (в pyrosm — 'id'), нужные теги, если они есть, и геометрию."""
    gdf = gdf.rename(columns={"id": "osm_id"})
    keep = [c for c in ["osm_id", *columns] if c in gdf.columns]
    return gdf[keep + ["geometry"]].copy()


def _tag(key: str):
    import json

    def get(tags):
        if tags is None or (isinstance(tags, float) and pd.isna(tags)):
            return None
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except ValueError:
                return None
        return tags.get(key) if isinstance(tags, dict) else None

    return get


def build_walk_graph(pbf_path: Path, boundary: gpd.GeoDataFrame, crs: int, speed_kmh: float = 5.0,
                     buffer_m: float = 1000) -> nx.MultiDiGraph:
    """Пешеходный граф в формате, который ожидает BlocksNet (как граф IduEdu).

    Требования BlocksNet (relations/accessibility/graph/schemas.py):
      * graph.graph['crs'] — int EPSG; * у узлов есть x, y (в этой CRS); * у рёбер есть 'time_min'.
    Граф строится с буфером вокруг границы, чтобы крайние кварталы не теряли связи.
    """
    from pyrosm import OSM

    area = boundary.to_crs(crs).buffer(buffer_m).to_crs(4326).union_all()
    osm = OSM(str(pbf_path), bounding_box=area)
    nodes, edges = osm.get_network(network_type="walking", nodes=True)
    edges = edges.to_crs(crs)
    nodes = nodes.to_crs(crs)

    graph = nx.MultiDiGraph()
    graph.graph["crs"] = int(crs)
    graph.graph["type"] = "walk"
    for node_id, geom in zip(nodes["id"], nodes.geometry):
        graph.add_node(int(node_id), x=float(geom.x), y=float(geom.y))

    metres_per_min = speed_kmh * 1000 / 60
    for u, v, geom in zip(edges["u"], edges["v"], edges.geometry):
        if u not in graph or v not in graph:
            continue
        length = float(geom.length)
        attrs = dict(length_meter=length, time_min=length / metres_per_min, type="walk", geometry=geom)
        # пешеходная сеть — двунаправленная
        graph.add_edge(int(u), int(v), **attrs)
        graph.add_edge(int(v), int(u), **attrs)

    # оставляем крупнейшую связную компоненту, чтобы не было «островов» с бесконечным временем
    largest = max(nx.weakly_connected_components(graph), key=len)
    graph = graph.subgraph(largest).copy()
    # IduEdu (а через него BlocksNet) использует id узлов как индексы строк разреженной матрицы,
    # поэтому узлы обязаны быть пронумерованы 0..N-1, как в графах IduEdu. С OSM-id — segfault.
    graph = nx.convert_node_labels_to_integers(graph, label_attribute="osm_id")
    logger.info(f"Пешеходный граф: {graph.number_of_nodes()} узлов, {graph.number_of_edges()} рёбер")
    return graph
