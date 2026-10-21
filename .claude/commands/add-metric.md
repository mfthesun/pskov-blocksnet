---
description: Добавить новый показатель по кварталам — ноутбук → GeoJSON → дашборд → сверка
argument-hint: <описание показателя>
---
Добавь показатель: $ARGUMENTS

Сначала **режим плана**: опиши, какая функция BlocksNet (или своя формула) считает показатель, единицы, оценочный ли он, где он будет в дашборде. Дождись подтверждения.

Затем:
1. Ноутбук `notebooks/pskov_blocksnet.ipynb`: markdown-объяснение простыми словами + ячейка расчёта (не выполняй тяжёлые ячейки без просьбы), добавь колонку в итоговый слой (раздел 14) и строку в сверку (раздел 15).
2. `scripts/build_dashboard.py`: поле в `BLOCK_FIELDS`.
3. `pskov_blocksnet/dashboard/template.html`: индикатор в `INDICATORS` и/или строка в панели квартала, запись в словаре показателей; бейдж `оценка`, если нужно.
4. `tests/test_results.py`: поле в `DASHBOARD_FIELDS`.
5. `docs/verification.md` и при необходимости `docs/findings.md`.
6. Скажи, какие команды выполнить: `make notebook && make dashboard && make check`.
