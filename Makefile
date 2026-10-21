# Команды проекта. Linux/macOS: make <цель>. Windows: команды из docs/rerun.md.
PY ?= python
NB = notebooks/pskov_blocksnet.ipynb

.PHONY: help venv install data notebook dashboard all check tests clean-cache format

help:
	@echo "make venv       — создать .venv (Python 3.10–3.12)"
	@echo "make install    — установить зависимости проекта в активное окружение"
	@echo "make data       — подготовить входные данные из PSKOKN (один раз; уже сделано)"
	@echo "make notebook   — выполнить ноутбук целиком (расчёты -> data/results)"
	@echo "make dashboard  — собрать dashboard.html из data/results"
	@echo "make all        — notebook + dashboard + check"
	@echo "make check      — проверить результаты и сверку ноутбук <-> дашборд"
	@echo "make clean-cache — удалить кэш графа и матрицы (пересчитать с нуля)"

venv:
	python3.12 -m venv .venv || python3 -m venv .venv
	@echo "Активируйте: source .venv/bin/activate"

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev,tests]"

data:
	$(PY) scripts/prepare_data.py

notebook:
	$(PY) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 $(NB)

dashboard:
	$(PY) scripts/build_dashboard.py

check tests:
	$(PY) -m pytest -q

all: notebook dashboard check

clean-cache:
	rm -rf data/cache

format:
	isort pskov_blocksnet scripts tests
	black pskov_blocksnet scripts tests
