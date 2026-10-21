---
description: Собрать dashboard.html из готовых GeoJSON (без расчётов)
---
1. Убедись, что `data/results/blocks.geojson` и `summary.json` существуют; если нет — скажи запустить `/run-notebook` и остановись.
2. Запусти `python scripts/build_dashboard.py` и покажи размер файла.
3. Запусти `python -m pytest -q`. Если тест упал — объясни причину и предложи исправление.
4. Напомни, как открыть: `dashboard.html` в браузере (нужен интернет только для подложек Esri/OSM).
Не скачивай данные и не меняй расчёты — дашборд только читает `data/results/`.
