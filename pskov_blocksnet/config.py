"""Единые настройки проекта: пути, территория, параметры моделей.

Все скрипты и ноутбук берут пути отсюда, чтобы не было «магических строк».
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Пути -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INPUT_DIR = DATA_DIR / "input"  # подготовленные входные слои (только г. Псков), лежат в git
OSM_DIR = DATA_DIR / "osm"  # слои OSM, извлечённые из PBF для г. Пскова, лежат в git
RESULTS_DIR = DATA_DIR / "results"  # результаты расчётов BlocksNet (GeoJSON), лежат в git
CACHE_DIR = DATA_DIR / "cache"  # тяжёлые промежуточные файлы (граф, матрица), НЕ в git
DASHBOARD_PATH = ROOT / "dashboard.html"

# Региональная выгрузка OSM (Псковская область, ~45 МБ) в репозиторий не кладётся.
# Путь можно переопределить переменной окружения PSKOV_PBF.
DEFAULT_PBF = Path.home() / "Claude" / "ИИ, анализ данных и моделирование в урбанистике" / "PSKOKN" / "данные и материалы" / "pskov_oblast.pbf"
PBF_PATH = Path(os.environ.get("PSKOV_PBF", DEFAULT_PBF))

# --- Территория -------------------------------------------------------------

CITY_NAME = "Псков"
TERRITORY_NAME = "городской округ Псков"
REGION_NAME = "Псковская область"
COUNTRY_NAME = "Россия"
# UTM-зона для Пскова (28.3° в. д.) — 35N. Метрические расчёты ведём в ней.
LOCAL_CRS = 32635

# --- Параметры моделей ------------------------------------------------------

WALK_SPEED_KMH = 5.0  # скорость пешехода для графа (как в примере Миасса)
DEFAULT_LIVING_DEMAND = 30  # м² жилой площади на человека (параметр impute_buildings)
SCHOOL_SERVICE = "school"  # тип сервиса BlocksNet для обеспеченности

# Теги зданий, которые считаем жилыми (как в pipeline.ipynb + частные дома)
IS_LIVING_TAGS = ["residential", "house", "apartments", "detached", "terrace", "dormitory", "semidetached_house"]

# Авторство подготовленных данных (выводится в дашборде и README)
DATA_AUTHORS = {
    "transport": "Виктор Цыганов",
    "heritage": "Денис Яковлев",
}
