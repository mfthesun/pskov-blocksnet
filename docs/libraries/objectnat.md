# ObjectNat 2.1 — пространственный и сетевой анализ

Репозиторий: https://github.com/IDUclub/ObjectNat · документация: https://iduclub.github.io/ObjectNat/

Работает с графами **IduEdu 2.x** (`UrbanGraph`). Блокноты курса (с параметрами в стиле Colab):
`~/Claude/ИИ, анализ данных и моделирование в урбанистике/Блокноты ObjectNAT/` + `Тестовые данные/`.

## Окружение (отдельное от BlocksNet!)

```bash
python3.12 -m venv .venv-objectnat && source .venv-objectnat/bin/activate
pip install "ObjectNat==2.1.0" "iduedu[io]==2.2.0" "folium>=0.19.5,<0.20" mapclassify matplotlib ipywidgets
```

## Методы

| Блокнот | Функции | Что даёт |
|---|---|---|
| `00_iduedu_urban_graphs` | `get_walk_graph`, `get_drive_graph`, `get_public_transport_graph`, `get_intermodal_graph`, `write_urban_graph` | граф территории → `graph.urbangraph` |
| `01_objectnat_coverage` | `get_graph_coverage`, `get_stepped_graph_coverage`, `get_radius_coverage` | зоны обслуживания сервисов (Voronoi по сети) |
| `02_objectnat_isochrones` | `get_graph_isochrones`, `get_stepped_graph_isochrones` | изохроны от точек: `geometry_type` = `radius` / `ways` / `separate` |
| `03_objectnat_provision` | `get_service_provision` → `ProvisionResult`, `get_provision_buildings` и др. | обеспеченность зданий сервисами (гравитационная модель, порог в мин/м) |
| `04_objectnat_visibility` | `get_visibility(point_from, obstacles, view_distance, method="accurate"/"simple")` | полигоны видимости |
| `05_objectnat_noise` | `simulate_noise`, `calculate_simplified_noise_frame` | распространение шума с учётом зданий и деревьев |

### Сигнатуры (2.1.0)

```python
get_graph_isochrones(urban_graph, *, weight_value_cutoff, gdf_origins=None, weight_type="time_min",
                     geometry_type="radius", zone=None, buffer_factor=0.7, road_buffer_size=5.0)
get_graph_coverage(urban_graph, *, gdf_destinations=None, weight_type="time_min", geometry_type=None,
                   weight_value_cutoff=None, zone=None)
get_service_provision(*, buildings, distance_matrix, services, threshold,
                      buildings_demand_column="demand", services_capacity_column="capacity")
get_visibility(point_from, obstacles, view_distance=None, method="accurate", *, resolution=32, parallel=False)
simulate_noise(source_points, obstacles, source_noise_db=None, geometric_mean_freq_hz=None, **kwargs)
```

## BlocksNet vs ObjectNat: обеспеченность

| | BlocksNet `competitive_provision` | ObjectNat `get_service_provision` |
|---|---|---|
| Единица | квартал | здание |
| Модель | линейная оптимизация (PuLP), сначала свой квартал | гравитационная, вес ~ 1/расстояние² |
| Порог | норматив доступности сервиса (школа — 15 мин) | `threshold` в мин или м |

## Идеи для Пскова

* Изохроны 10/15/20 мин пешком от школ и от остановок → сравнить с `provision_strong`.
* Зоны покрытия школ (coverage) → наглядная альтернатива потокам.
* Видимость доминант (соборы Кремля, церкви ЮНЕСКО) — связка с темой ОКН.
* Входные данные можно брать из `data/osm/` и `data/input/` этого репозитория.
