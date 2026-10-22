# Инструкция повторного запуска

## 1. Окружение

Нужен Python **3.10–3.12** (зависимость `iduedu==0.4.1` не ставится на 3.13+).

**Linux / macOS**

```bash
cd pskov-blocksnet
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,tests]"
```

**Если в системе нет Python 3.12** (например, Ubuntu с Python 3.14) — через [uv](https://docs.astral.sh/uv/), без sudo:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env
uv venv -p 3.12 .venv            # uv сам скачает Python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,tests]" # в .venv от uv нет pip — ставить только через `uv pip`
```

**Windows (PowerShell)**

```powershell
cd pskov-blocksnet
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,tests]"
```

Как в задании, можно поставить BlocksNet отдельно: `pip install "blocksnet[ipynb,torch]==1.0.0a9"`
(+ `pip install pyrosm pyogrio jupyter`).

Проверка: `python -c "import importlib.metadata as m; print(m.version('blocksnet'))"` → `1.0.0a9`.

## 2. Только пересобрать страницу (секунды)

```bash
python scripts/build_dashboard.py      # -> dashboard.html
python -m pytest -q                    # проверки
```

Страница читает `data/results/*.geojson` и `summary.json`. Ничего не скачивается и не пересчитывается.

## 3. Пересчитать показатели (≈ 15 с с кэшем, ≈ 1 мин без кэша)

```bash
make notebook        # = jupyter nbconvert --to notebook --execute --inplace notebooks/pskov_blocksnet.ipynb
make dashboard
make check
```

или откройте ноутбук в VS Code / Jupyter и выполните ячейки по порядку (на 🛑 стоп-точках проверьте карты).

* Граф и матрица доступности кэшируются в `data/cache/` (в git не попадает). Чтобы посчитать заново — `make clean-cache`.
* Без кэша граф строится из `data/osm/pskov_city.osm.pbf` — файл в репозитории, интернет не нужен.
  Другой PBF: `export PSKOV_PBF=/путь/к/файлу.pbf` (Windows: `$env:PSKOV_PBF="C:\...\файл.pbf"`).

### Онлайн-режим (как в pipeline.ipynb)

В первой ячейке ноутбука: `DATA_MODE = "osm"`, при желании `GRAPH_TYPE = "intermodal"`. Данные скачиваются через
`osmnx`, граф — через IduEdu (Overpass API). Нужен интернет, займёт 5–20 минут, результат зависит от текущего OSM и
будет немного отличаться от сохранённого.

## 4. Подготовить входные данные заново (редко)

Только если обновились исходники (новая выгрузка OSM, новая версия реестра ОКН):

```bash
python scripts/prepare_data.py --source "<папка PSKOKN>" [--pbf <путь к pskov_oblast.pbf>]   # нужен osmium-tool для вырезки
```

## 5. Через Claude Code

```bash
claude                      # в корне репозитория; CLAUDE.md подхватится автоматически
```

* `/run-notebook` — пересчёт; `/build-dashboard` — сборка страницы; `/verify` — сверка; `/push-github <адрес>` — публикация.

## Частые ошибки

| Ошибка | Причина и решение |
|---|---|
| `No matching distribution found for iduedu==0.4.1` | Python 3.13+ → создайте окружение на 3.12 |
| `ModuleNotFoundError: No module named 'torch'` | не установлен extra: `pip install "blocksnet[torch]==1.0.0a9"` |
| `File does not exist: ...pbf` | нет `data/osm/pskov_city.osm.pbf` (удалён) или неверный `PSKOV_PBF` |
| Segmentation fault в `calculate_accessibility_matrix` | граф с OSM-id узлов → используйте `build_walk_graph` (перенумеровывает узлы) |
| Пустая карта в `dashboard.html` | подложки грузятся из интернета; кварталы видны и без подложки |
