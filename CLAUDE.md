# CLAUDE.md — инструкции для Claude Code

Учебный проект: квартальная модель **г. Пскова** на **BlocksNet 1.0.0a9** + интерактивный дашборд.
Практика 2 дисциплины «Технологии ИИ в урбанистике» (ИДУ ИТМО). Авторы — Яковлев Д. А., Цыганов В. А. (C4207).
Задание: https://mvin8.github.io/ai-technologies-in-urbanism/content/practice/practice-02.html
(в задании агент — OpenCode; преподаватель разрешил любой агент, здесь — Claude Code).

Отвечай и пиши документацию **по-русски**.

## Конвейер (порядок важен)

```
scripts/prepare_data.py   PBF + материалы PSKOKN  ->  data/input/*.geojson, data/osm/*.geojson   (один раз, уже сделано)
notebooks/pskov_blocksnet.ipynb   data/input + data/osm  ->  data/results/*.geojson + summary.json  (все расчёты)
scripts/build_dashboard.py        data/results  ->  dashboard.html                                    (только сборка)
```

Команды — в `Makefile`: `make install`, `make notebook`, `make dashboard`, `make check`, `make all`.

## Жёсткие правила

1. **`build_dashboard.py` не скачивает данные и не считает метрики.** Он только читает `data/results/` и
   встраивает их в шаблон `pskov_blocksnet/dashboard/template.html`. Новый показатель сначала считается
   в ноутбуке и сохраняется в `blocks.geojson`, потом выводится в дашборд.
2. **Каждый показатель дашборда должен быть в ноутбуке** — и наоборот (требование задания). После изменений
   обнови сверочную таблицу в разделе 15 ноутбука и `docs/verification.md`, запусти `make check`.
3. **Не запускай тяжёлые ячейки без запроса.** Загрузка из Overpass (`DATA_MODE="osm"`) и построение графа
   идут минутами; по умолчанию режим `pbf` и кэш `data/cache/`. Если пользователь просит «подготовить ячейки» —
   пиши код, но не выполняй.
4. **Оценочные значения помечай** (население, вместимость школ, этажность-по-умолчанию) — в ноутбуке, в
   дашборде (бейдж `оценка`) и в `docs/findings.md`.
5. **Источники и авторство данных:** транспорт (остановки) — **Виктор Цыганов**; ОКН и зоны охраны —
   **Денис Яковлев**. Указывать в дашборде, README и `docs/data.md`.
6. **Подложки карт:** Esri (World Light Gray, World Imagery, World Topo, World Street) и OpenStreetMap.
   **Не используй CARTO** (нужен API-ключ).
7. **Git:** без `push --force`, без переписывания истории; не коммить `.env`, `.venv/`, `data/cache/`, `*.pbf`.
8. Не устанавливай другие версии `blocksnet`/`iduedu` в это окружение: BlocksNet 1.0.0a9 жёстко требует
   `iduedu==0.4.1` (NetworkX API). ObjectNat 2.x требует `iduedu>=2.2` — это **отдельное** окружение
   (см. `docs/libraries/objectnat.md`).

## Окружение

* Python **3.10–3.12** (iduedu 0.4.1 не ставится на 3.13+). Создание: `make venv && source .venv/bin/activate && make install`.
* BlocksNet импортирует `torch` уже при `from blocksnet.blocks.cutting import ...` → нужен extra `[torch]`.
* Пешеходный граф строится из `data/osm/pskov_city.osm.pbf` (вырезка по городу, лежит в git; переопределить — `PSKOV_PBF`).
  Региональный `pskov_oblast.pbf` нужен только `prepare_data.py`.

## Где что лежит

| Путь | Что |
|---|---|
| `pskov_blocksnet/config.py` | пути, CRS (EPSG:32635), параметры моделей, авторы данных |
| `pskov_blocksnet/osm_pbf.py` | извлечение слоёв OSM из PBF (pyrosm), пешеходный граф в формате IduEdu |
| `pskov_blocksnet/io.py` | запись/чтение GeoJSON |
| `pskov_blocksnet/dashboard/` | HTML-шаблон дашборда + встроенный Leaflet 1.9.4 |
| `notebooks/pskov_blocksnet.ipynb` | все расчёты BlocksNet с пояснениями, стоп-точки, выводы |
| `data/results/` | результаты (GeoJSON, `summary.json`) — источник для дашборда |
| `docs/` | план, запросы, перезапуск, выводы, сверка, данные, шпаргалки по библиотекам |
| `.claude/commands/` | слэш-команды проекта (`/run-notebook`, `/build-dashboard`, `/verify`, `/push-github`, `/add-metric`) |

## Известные подводные камни (проверено)

* Граф для `calculate_accessibility_matrix`: `graph.graph["crs"]` — int EPSG, у узлов `x`,`y`, у рёбер `time_min`,
  **узлы пронумерованы 0..N-1** (IduEdu использует id как индекс CSR-матрицы; с OSM-id — segfault).
* `aggregate_objects` возвращает счётчик в колонке `count` (не `objects_count`).
* `area_accessibility` в 1.0.0a9 лежит в `blocksnet.analysis.network.accessibility` (в pipeline.ipynb — старый путь).
* `assign_land_use` возвращает в `land_use` enum `LandUse` → для GeoJSON переводить в `.value`.
* `calculate_density_indicators` даёт `osr = inf` для кварталов без застройки → заменять на NaN.

## Стиль

Код — black/isort, длина строки 120. Комментарии и markdown — по-русски, кратко, «почему», а не «что».
