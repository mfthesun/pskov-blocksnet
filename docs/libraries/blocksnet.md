# BlocksNet 1.0.0a9 — шпаргалка

Репозиторий: https://github.com/aimclub/blocksnet · примеры: `examples/` · установка:

```bash
pip install "blocksnet[ipynb,torch]==1.0.0a9"   # Python 3.10–3.12
```

**Идея.** Город описывается как набор **кварталов** (urban blocks) — полигонов, ограниченных улицами, ж/д и водой.
Любые данные (здания, сервисы, функциональные зоны) агрегируются в кварталы, связи между кварталами задаются
матрицей времени в пути. На этом строятся индикаторы, обеспеченность, морфотипы, оптимизация и ML.

## Зависимости и подводные камни версии 1.0.0a9

| Что | Деталь |
|---|---|
| `iduedu==0.4.1` | жёсткий пин; NetworkX-API IduEdu; **Python < 3.13**. Несовместим с ObjectNat 2.x (нужен iduedu ≥ 2.2) |
| `torch` | импортируется уже в `blocksnet.blocks.cutting` (через `BlocksClassifier`) → extra `[torch]` обязателен |
| `pyarrow<20`, `pandera==0.20.2`, `PuLP==2.7.0` | старые пины — лучше отдельное окружение |
| Логи | `loguru`, много INFO; приглушить: `from loguru import logger; logger.remove(); logger.add(sys.stderr, level="WARNING")` |

## Конвейер (как в `examples/pipeline.ipynb`)

### 1. Нарезка кварталов — `blocksnet.blocks.cutting`

```python
from blocksnet.blocks.cutting import preprocess_urban_objects, cut_urban_blocks
from blocksnet.blocks.postprocessing import postprocess_urban_blocks

lines, polygons = preprocess_urban_objects(roads_gdf, railways_gdf, water_gdf)   # любые могут быть None
blocks = cut_urban_blocks(boundaries_gdf, lines, polygons)                        # GeoDataFrame[geometry]
blocks = postprocess_urban_blocks(blocks)                                         # чинит невалидные, explode
```

* Все слои в **одной метрической CRS** (`boundaries.estimate_utm_crs()`).
* Дороги и ж/д — линии; вода — полигоны и линии (линии воды режут, полигоны вычитаются).
* `cut_urban_blocks(..., buildings_gdf, classifier=BlocksClassifier.default())` — дополнительно делит слишком крупные
  кварталы по зданиям (см. `examples/blocks/cutting.ipynb`).
* Получаются «осколки» в доли м² — имеет смысл отфильтровать по площади (у нас < 100 м²).

### 2. Землепользование — `blocksnet.blocks.assignment`

```python
from blocksnet.enums import LandUse     # RESIDENTIAL, BUSINESS, RECREATION, INDUSTRIAL, TRANSPORT, SPECIAL, AGRICULTURE
from blocksnet.blocks.assignment import assign_land_use

zones = landuse_gdf.rename(columns={"landuse": "functional_zone"})[["functional_zone", "geometry"]]
rules = {"residential": LandUse.RESIDENTIAL, "commercial": LandUse.BUSINESS, ...}
blocks_lu = assign_land_use(blocks, zones, rules)
```

Возвращает доли каждой функции (`residential`, …, 0–1) и `land_use` — преобладающую (enum `LandUse` или `None`).
Для GeoJSON: `blocks_lu.land_use.apply(lambda v: v.value if v else None)`.

### 3. Связи между кварталами — `blocksnet.relations`

```python
from blocksnet.relations import get_accessibility_graph, calculate_accessibility_matrix

graph = get_accessibility_graph(boundaries_gdf, "intermodal")   # "walk" | "drive" | "intermodal" — через IduEdu (Overpass)
acc_mx = calculate_accessibility_matrix(blocks, graph)           # DataFrame n×n, минуты, float16
```

**Свой граф** (например, из PBF) подходит, если:
`graph.graph["crs"]` — int EPSG; у узлов есть `x`, `y` в этой CRS; у рёбер — `time_min`;
**узлы пронумерованы 0..N-1** (`nx.convert_node_labels_to_integers`) — иначе segfault в numba-Дейкстре IduEdu.
Время включает подход от точки квартала до ближайшего узла со скоростью 5 км/ч.
Также есть `calculate_distance_matrix` и `calculate_adjacency_graph`.

### 4. Здания — `preprocessing.imputing` + `blocks.aggregation`

```python
from blocksnet.preprocessing.imputing import impute_buildings
from blocksnet.blocks.aggregation import aggregate_objects

buildings["is_living"] = buildings["building"].isin(["residential", "house", "apartments", "detached", "terrace", "dormitory"])
buildings["number_of_floors"] = pd.to_numeric(buildings["building:levels"], errors="coerce")
buildings = impute_buildings(buildings, default_living_demand=30)   # м²/чел.
buildings_blocks = aggregate_objects(blocks, buildings)[0]          # суммы по кварталам + колонка count
```

`impute_buildings(default_number_of_floors=1, living_area_coefficient=0.9, default_living_demand=20)`:
footprint = площадь контура → floors = 1 при пропуске → build_floor_area = floors × footprint →
living = 0,9 × bfa (только жилые) → non_living = bfa − living → population = living // demand (минимум 1).

### 5. Сервисы

```python
from blocksnet.preprocessing.imputing import impute_services
from blocksnet.config import service_types_config

schools = impute_services(schools_gdf[["capacity", "geometry"]], "school")   # пропуски capacity → min типовой единицы (250)
service_types_config["school"]   # {'name_ru': 'школа', 'demand': 120, 'accessibility': 15}
schools_blocks = aggregate_objects(blocks, schools)[0]                      # capacity, count
```

Справочник типов сервисов и типовых единиц: `blocksnet/config/service_types/common/default.json`.

### 6. Обеспеченность — `analysis.provision`

```python
from blocksnet.analysis.provision import competitive_provision
df = buildings_blocks[["population"]].join(schools_blocks[["capacity"]])
prov_df, links_df = competitive_provision(df, acc_mx, accessibility=15, demand=120)
```

`prov_df`: `demand`, `capacity`, `demand_within` (в норме доступности), `demand_without` (за нормой, при
`max_depth>1`), `demand_left`, `capacity_left`, `provision_strong`, `provision_weak`. `links_df` — потоки
(source, target) → value. Решается PuLP/CBC. Есть также `shared_provision`.

### 7. Плотность — `analysis.indicators`

```python
from blocksnet.analysis.indicators import calculate_density_indicators
buildings_blocks["site_area"] = buildings_blocks.area
density = calculate_density_indicators(buildings_blocks)   # fsi, gsi, mxi, l, osr, share_living, share_non_living
```

`osr = inf` у пустых кварталов → `replace([inf, -inf], nan)`. В `indicators/socio_economic/*` — ещё
демографические, экономические, транспортные и пр. индикаторы.

### 8. Морфотипы — `analysis.morphotypes`

```python
from blocksnet.analysis.morphotypes import get_spacematrix_morphotypes, get_strelka_morphotypes
sm_df, sm_clusters = get_spacematrix_morphotypes(density)   # k-means по l, fsi, mxi; morphotype + cluster
st_df = get_strelka_morphotypes(density)                    # правила КБ «Стрелка»
```

### 9. Доступность — `analysis.network.accessibility`

```python
from blocksnet.analysis.network.accessibility import area_accessibility   # в pipeline.ipynb старый путь analysis.accessibility
area_acc = area_accessibility(acc_mx, buildings_blocks)   # нужна колонка site_area; среднее время, взвешенное по площади
```

Там же: `land_use_accessibility`, `relative_accessibility`, базовые функции.

## Другие модули (на будущее)

| Модуль | Что умеет |
|---|---|
| `analysis.diversity` | индекс Шеннона по сервисам/функциям |
| `analysis.services` | плотность и число сервисов, коллокация |
| `analysis.land_use` | доли, сходство, коллокация, прогноз функций |
| `analysis.centrality` | центральность по населению и сервисам |
| `analysis.network` | связность, OD-матрицы, загрузка дорог |
| `analysis.vacant_area` | свободные участки |
| `optimization.land_use / services` | подбор функций и сервисов под нормативы |
| `synthesis.services_planning` | генерация размещения сервисов |
| `machine_learning` | классификация кварталов, регрессия плотности и соц. показателей (torch, catboost, xgboost) |

Примеры для каждого — `examples/analysis/*`, `examples/optimization/*`, `examples/machine_learning/*`.
