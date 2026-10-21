# IduEdu — графы городских сетей

Репозиторий: https://github.com/IDUclub/IduEdu · документация: https://iduclub.github.io/IduEdu/

Строит пешеходные, автомобильные, транспортные (ОТ) и **интермодальные** графы из OpenStreetMap (Overpass)
и GTFS; считает кратчайшие пути и OD-матрицы (numba).

## Две несовместимые линии версий

| | **0.4.1** | **2.2.0** (актуальная) |
|---|---|---|
| Кто требует | BlocksNet 1.0.0a9 (`iduedu==0.4.1`) | ObjectNat 2.1.0 (`iduedu>=2.2`) |
| Python | 3.10–3.12 | 3.11–3.14 |
| Тип графа | `networkx.MultiDiGraph` (`graph.graph["crs"]`, узлы `x`,`y`, рёбра `time_min`, `length_meter`) | `UrbanGraph` (`nodes_gdf`, `edges_gdf`), конвертация в NetworkX — опционально |
| Матрица | `get_adj_matrix_gdf_to_gdf(gdf_from, gdf_to, graph, weight)` | `od_matrix(...)` |
| Сохранение | pickle | `write_urban_graph(G, "graph.urbangraph")` / `read_urban_graph` (extra `[io]`) |

**Вывод:** BlocksNet и ObjectNat — в разных окружениях. Обмен данными — через файлы (GeoJSON / parquet / `.urbangraph`).

## 0.4.1 (в этом проекте, через BlocksNet)

```python
import iduedu as ie
g_walk = ie.get_walk_graph(polygon=shapely_polygon_4326)
g_drive = ie.get_drive_graph(polygon=...)
g_inter = ie.get_intermodal_graph(polygon=...)          # пешеход + ОТ из OSM-маршрутов
mx = ie.get_adj_matrix_gdf_to_gdf(blocks, blocks, g_walk, "time_min")
```

Внутри: id узлов используются как индексы CSR-матрицы → **узлы должны быть 0..N-1**. Пустые/висячие компоненты
удаляются `remove_weakly_connected_nodes`. Время подхода к узлу добавляется по 5 км/ч.

## 2.2.0 (в блокнотах курса, `Блокноты ObjectNAT/00_iduedu_urban_graphs.ipynb`)

```python
from iduedu import get_walk_graph, get_drive_graph, get_public_transport_graph, get_intermodal_graph, write_urban_graph
G = get_intermodal_graph(osm_id=1114252, pt_kwargs={"transport_types": ["bus", "tram", "subway"]})
G.nodes_gdf, G.edges_gdf          # рёбра: u, v, geometry, length_meter, time_min
G.validate()
write_urban_graph(G, "graph.urbangraph")
```

GTFS: `get_gtfs_public_transport_graph("feed.zip", service_date=..., start_time=..., end_time=...)`.

## Для Пскова

* OSM relation ГО Псков можно найти по `wikidata` из `data/input/boundary.geojson`.
* Overpass недоступен из облачной среды агента, поэтому в проекте граф строится офлайн из PBF
  (`pskov_blocksnet/osm_pbf.py::build_walk_graph`) в формате 0.4.1.
* Для интермодального графа Пскова: локально `DATA_MODE="osm"`, `GRAPH_TYPE="intermodal"` в ноутбуке.
