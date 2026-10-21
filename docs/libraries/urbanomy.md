# Urbanomy — экономика территорий

Репозиторий: https://github.com/IDUclub/Urbanomy (локальная копия: `~/Projects/Urbanomy`) ·
лекция курса: `Urbanomy - Лекция.pdf` в проекте.

Оценка участков и кварталов с пространственной, экономической и сценарной точек зрения.

## Модули

| Модуль | Что делает |
|---|---|
| `urbanomy.methods.land_value_modeling` | `LandDataPreparator` (пространственные лаги, матрица доступности) → `LandPriceEstimator` (предобученная CatBoost) → `plot_land_price_maps` — **модельная цена земли** |
| `...land_value_modeling.scenario_modification` | что-если: изменить кварталы, пересчитать индикаторы и цены |
| `urbanomy.methods.investment_potential` | `LandUseScoreAnalyzer`, `prepare_investment_input`, `InvestmentAttractivenessAnalyzer` — NPV/IRR/ROI, индекс INV |
| `urbanomy.methods.ser` | `SEREstimator` — налоговые и занятостные эффекты стройки и эксплуатации |
| `urbanomy.utils` | Pandera-схемы входных данных |

## Окружение

Требует **Python 3.10** (строго `>=3.10,<3.11`). Ставится из исходников: `pip install -e .` в папке репозитория.
С BlocksNet 1.0.0a9 по версии Python совместим (3.10), но набор зависимостей большой — лучше отдельное окружение.

## Связь с практикой 2

В примере дашборда Миасса есть показатель «Модельная цена земли, ₽ за сотку» — это, судя по всему, результат
`land_value_modeling` Urbanomy поверх кварталов BlocksNet (вход — кварталы + матрица доступности). В
`pipeline.ipynb` его нет, поэтому в обязательную часть не входит. Для Пскова это естественный следующий шаг:
`data/results/blocks.geojson` + матрица из `data/cache/` → `LandDataPreparator` → цена по кварталам
(с оговоркой, что модель обучена не на Пскове и её точность здесь не оценивалась).

Пример лаунчера: `examples/` в репозитории Urbanomy.
