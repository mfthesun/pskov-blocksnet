"""Проверки результатов: всё, что показывает дашборд, есть в сохранённых GeoJSON и в ноутбуке.

Запуск: make check  (или python -m pytest -q)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
NOTEBOOK = ROOT / "notebooks" / "pskov_blocksnet.ipynb"
TEMPLATE = ROOT / "pskov_blocksnet" / "dashboard" / "template.html"
BUILD = ROOT / "scripts" / "build_dashboard.py"

# колонка blocks.geojson -> короткое имя в дашборде (см. BLOCK_FIELDS в build_dashboard.py)
DASHBOARD_FIELDS = {
    "land_use": "lu", "population": "pop", "population_density": "pop_dens", "fsi": "fsi", "gsi": "gsi",
    "l": "floors", "mxi": "mxi", "osr": "osr", "area_accessibility": "acc", "provision_strong": "prov",
    "provision_weak": "prov_weak", "demand": "demand", "demand_within": "d_within", "demand_without": "d_without",
    "demand_left": "d_left", "capacity_left": "cap_left", "schools_count": "sch", "schools_capacity": "sch_cap",
    "spacematrix_morphotype": "sm", "strelka_morphotype": "st", "okn_count": "okn", "protection_zone_share": "pz",
    "nearest_stop_m": "stop_m", "footprint_area": "footprint", "build_floor_area": "bfa",
    "living_area": "living", "non_living_area": "nonliving", "living_buildings": "bld_liv",
}


@pytest.fixture(scope="module")
def blocks():
    return gpd.read_file(RESULTS / "blocks.geojson")


def test_result_files_exist():
    for name in ["blocks", "schools", "provision_links", "boundary", "heritage_points",
                 "heritage_protection_zones", "transport_stops"]:
        assert (RESULTS / f"{name}.geojson").exists(), name
    assert (RESULTS / "summary.json").exists()


def test_blocks_have_all_dashboard_columns(blocks):
    missing = [c for c in DASHBOARD_FIELDS if c not in blocks.columns]
    assert not missing, f"нет колонок: {missing}"


def test_values_are_plausible(blocks):
    assert len(blocks) > 500
    assert blocks.crs.to_epsg() == 4326
    assert (blocks.fsi.fillna(0) >= 0).all()
    assert blocks.provision_strong.dropna().between(0, 1).all()
    assert blocks.area_accessibility.between(0, 300).all()
    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    pop = summary["totals"]["population"]
    assert pop == int(blocks.population.sum())
    # расчётное население в пределах ±30 % от тега OSM — грубая проверка здравого смысла
    assert 0.7 < pop / summary["totals"]["population_osm_tag"] < 1.3


def test_dashboard_template_uses_fields():
    template = TEMPLATE.read_text(encoding="utf-8")
    build = BUILD.read_text(encoding="utf-8")
    for col, short in DASHBOARD_FIELDS.items():
        assert f'"{col}": ("{short}"' in build, f"{col} не передаётся в дашборд"
        assert re.search(rf"\b{short}\b", template), f"{short} не используется в шаблоне"


def test_notebook_computes_fields():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    for fn in ["cut_urban_blocks", "assign_land_use", "calculate_accessibility_matrix", "impute_buildings",
               "aggregate_objects", "impute_services", "competitive_provision", "calculate_density_indicators",
               "get_spacematrix_morphotypes", "get_strelka_morphotypes", "area_accessibility"]:
        assert fn in code, f"в ноутбуке нет вызова {fn}"


def test_dashboard_builds(tmp_path):
    out = tmp_path / "dashboard.html"
    subprocess.run([sys.executable, str(BUILD), "-o", str(out)], check=True, cwd=ROOT)
    html = out.read_text(encoding="utf-8")
    assert "/*__DATA__*/" not in html and "L.map(" in html
    assert "carto" not in html.lower(), "подложки CARTO не используем"
    assert "Виктор Цыганов" in html and "Денис Яковлев" in html
