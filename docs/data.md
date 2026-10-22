# Данные

Все слои обрезаны по границе **городского округа Псков**; из материалов проекта PSKOKN по области взято только то,
что нужно для расчётов. Формат — GeoJSON, EPSG:4326 (метрические расчёты — в EPSG:32635, UTM 35N).

## Входные данные (`data/input/`)

| Файл | Объектов | Источник | Подготовка |
|---|---|---|---|
| `boundary.geojson` | 1 | граница ГО Псков, OSM (тег `population` = 209 426) | проект PSKOKN |
| `heritage_points.geojson` | 435 | ОКН — точки (категория, тип, ЮНЕСКО, особо ценные) | **Денис Яковлев** |
| `heritage_polygons.geojson` | 438 | ОКН — контуры (обрезаны по границе) | **Денис Яковлев** |
| `heritage_protection_zones.geojson` | 22 | зоны охраны ОКН (обрезаны по границе) | **Денис Яковлев** |
| `transport_stops.geojson` | 268 | остановки OSM `highway=bus_stop` (255), Яндекс.Расписания (8), ж/д платформы/станции (5) | **Виктор Цыганов** |

Источник слоёв ОКН и зон охраны — материалы по обоснованию схемы территориального планирования (СТП) Псковской области 2025 г. (выгрузка — `PSKOKN/данные и материалы/OKN_Pskov_Region.gpkg`).
Остановки — `transport_data.gpkg`, граница — `PSKOKN/boundaries/`.

## Слои OSM (`data/osm/`)

Извлечены из `pskov_oblast.pbf` (выгрузка OSM по Псковской области, © участники OpenStreetMap, лицензия ODbL)
библиотекой `pyrosm` — см. `pskov_blocksnet/osm_pbf.py`. Теги совпадают с `pipeline.ipynb`.

| Файл | Объектов | Теги |
|---|---|---|
| `roads.geojson` | 2 195 | `highway` ∈ список из `pipeline.ipynb` (линии) |
| `railways.geojson` | 252 | `railway=rail` |
| `water.geojson` | 116 | `natural=water/bay`, `waterway=river/canal/ditch/riverbank/dock`, `landuse=basin/reservoir`, `water=*` |
| `landuse.geojson` | 1 183 | `landuse=*` |
| `buildings.geojson` | 15 265 | `building=*` (+ `building:levels`, адрес, `start_date`) |
| `pskov_city.osm.pbf` | ≈ 2,5 МБ | вырезка `pskov_oblast.pbf` по границе + 1,5 км (`osmium extract --strategy complete_ways`) — источник пешеходного графа |
| `schools.geojson` | 42 | `amenity=school`; исключены футбольная школа, «Кибершкола», центр внешкольной работы; дубли «точка в контуре» |

## Результаты (`data/results/`)

| Файл | Что |
|---|---|
| `blocks.geojson` | 902 квартала, 43 показателя (см. `verification.md`) |
| `schools.geojson` | школы: название, вместимость, флаг `capacity_is_estimated` |
| `provision_links.geojson` | потоки «квартал → квартал со школой», число детей |
| `boundary`, `heritage_points`, `heritage_protection_zones`, `transport_stops` | контекстные слои для дашборда |
| `summary.json` | итоги по городу, параметры моделей, правила землепользования, кластеры Spacematrix, авторы данных |

## Не входит в репозиторий

* `pskov_oblast.pbf` (≈ 45 МБ) — нужен только `scripts/prepare_data.py`.
* `data/cache/` — граф (≈ 45 тыс. узлов) и матрица 902 × 902 (пересоздаются ноутбуком).
* Прочие материалы PSKOKN (турсхема, БД ПМО, отрисованные карты, шрифты) — к этой задаче не относятся.

## Качество данных OSM по Пскову

* Этажность (`building:levels`) указана у **17,8 %** зданий.
* У ≈ 73 % зданий `building=yes` — тип не указан, BlocksNet считает их нежилыми.
* Функциональные зоны покрывают город не полностью: 183 квартала без преобладающей функции.
* Тег `capacity` есть у 1 школы из 42.
