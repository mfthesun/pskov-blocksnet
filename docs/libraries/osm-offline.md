# OSM без Overpass: pyrosm и PBF

Зачем: `osmnx.features_from_polygon` и IduEdu ходят в Overpass API — это медленно, бывают лимиты и таймауты,
а результат меняется со временем. Если есть выгрузка `.osm.pbf` (Geofabrik или своя), слои берутся локально.

```python
from pyrosm import OSM
osm = OSM("pskov_oblast.pbf", bounding_box=boundary.to_crs(4326).union_all())

roads = osm.get_data_by_custom_criteria(custom_filter={"highway": [...]}, filter_type="keep",
                                        keep_nodes=False, keep_relations=False)
landuse = osm.get_landuse()
buildings = osm.get_buildings()
nodes, edges = osm.get_network(network_type="walking", nodes=True)   # "driving", "cycling", "all"
```

Особенности:

* id объекта — колонка `id` (не `osm_id`); редкие теги лежат в JSON-колонке `tags`.
* `bounding_box` с полигоном режет по bbox, а не по контуру → после чтения фильтровать `intersects(polygon)`.
* Отношения на границе bbox возвращаются с неполной геометрией (предупреждение) — для внутригородских задач некритично.
* Сеть: рёбра с `u`, `v`, `length`; для BlocksNet см. `pskov_blocksnet/osm_pbf.py::build_walk_graph`
  (двунаправленные рёбра, `time_min`, крупнейшая компонента, узлы 0..N-1).

Альтернативы: `osmium` (быстрая фильтрация/обрезка PBF: `osmium extract -p boundary.geojson in.pbf -o city.pbf`),
`osmnx.graph_from_xml` для `.osm` XML.
