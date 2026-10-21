"""Сборка dashboard.html из готовых результатов (data/results/*.geojson + summary.json).

Скрипт НЕ скачивает данные и НЕ повторяет расчёты BlocksNet — только читает сохранённые файлы,
переводит подписи на русский, округляет числа и встраивает всё в один HTML-файл по шаблону
pskov_blocksnet/dashboard/template.html.

Запуск из корня репозитория:
    python scripts/build_dashboard.py            # -> dashboard.html
    python scripts/build_dashboard.py -o out.html
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pskov_blocksnet import config  # noqa: E402

TEMPLATE = config.ROOT / "pskov_blocksnet" / "dashboard" / "template.html"
VENDOR = TEMPLATE.parent / "vendor"

LAND_USE_RU = {
    "residential": "Жилое", "business": "Деловое", "recreation": "Рекреационное", "industrial": "Промышленное",
    "transport": "Транспортное", "special": "Специальное", "agriculture": "Сельскохозяйственное",
}
STRELKA_RU = {
    "individual residential": "Индивидуальная жилая", "low-rise model": "Малоэтажная модельная",
    "low-rise non-residential": "Малоэтажная нежилая", "mid-rise": "Среднеэтажная",
    "mid-rise block": "Среднеэтажная квартальная", "mid-rise non-residential": "Среднеэтажная нежилая",
    "central model": "Центральная модель", "high-rise soviet microdistrict": "Советский микрорайон",
    "high-rise modern microdistrict": "Современный микрорайон",
}
SPACEMATRIX_WORDS = [
    ("high-mid-rise", "повышенной этажности"), ("high-rise", "многоэтажная"), ("mid-rise", "среднеэтажная"),
    ("low-rise", "малоэтажная"), ("high-density", "высокой плотности"), ("low-density", "низкой плотности"),
    ("non-residential", "нежилая"), ("mixed-use", "смешанная"), ("residential", "жилая"),
]

# колонка -> (новое имя, число знаков после запятой | None для строк)
BLOCK_FIELDS = {
    "block_id": ("id", 0), "site_area_ha": ("area_ha", 2), "land_use": ("lu", None),
    "residential": ("lu_res", 3), "business": ("lu_bus", 3), "recreation": ("lu_rec", 3),
    "industrial": ("lu_ind", 3), "transport": ("lu_tra", 3), "special": ("lu_spe", 3), "agriculture": ("lu_agr", 3),
    "buildings_count": ("bld", 0), "living_buildings": ("bld_liv", 0), "footprint_area": ("footprint", 0),
    "build_floor_area": ("bfa", 0), "living_area": ("living", 0), "non_living_area": ("nonliving", 0),
    "population": ("pop", 0), "population_density": ("pop_dens", 1),
    "schools_count": ("sch", 0), "schools_capacity": ("sch_cap", 0), "demand": ("demand", 0),
    "demand_within": ("d_within", 0), "demand_without": ("d_without", 0), "demand_left": ("d_left", 0),
    "capacity_left": ("cap_left", 0), "provision_strong": ("prov", 3), "provision_weak": ("prov_weak", 3),
    "fsi": ("fsi", 3), "gsi": ("gsi", 3), "mxi": ("mxi", 3), "l": ("floors", 2), "osr": ("osr", 2),
    "spacematrix_morphotype": ("sm", None), "strelka_morphotype": ("st", None),
    "area_accessibility": ("acc", 1), "okn_count": ("okn", 0), "okn_federal": ("okn_fed", 0),
    "okn_unesco": ("okn_unesco", 0), "protection_zone_share": ("pz", 3), "stops_count": ("stops", 0),
    "nearest_stop_m": ("stop_m", 0),
}


def spacematrix_ru(value: str | None) -> str | None:
    if not value:
        return None
    out = value
    for en, ru in SPACEMATRIX_WORDS:
        out = out.replace(en, ru)
    return out[0].upper() + out[1:]


def clean(value, digits):
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    if digits is None:
        return str(value)
    if digits == 0:
        return int(round(float(value)))
    return round(float(value), digits)


def to_features(gdf: gpd.GeoDataFrame, fields: dict[str, tuple[str, int | None]], precision: int = 5) -> dict:
    gdf = gdf.to_crs(4326)
    feats = []
    geo = json.loads(gdf.geometry.to_json(to_wgs84=True))["features"]
    for (_, row), g in zip(gdf.iterrows(), geo):
        props = {new: clean(row.get(col), d) for col, (new, d) in fields.items() if col in gdf.columns}
        feats.append({"type": "Feature", "properties": props, "geometry": _round_geom(g["geometry"], precision)})
    return {"type": "FeatureCollection", "features": feats}


def _round_geom(geom: dict, p: int) -> dict:
    def rnd(c):
        return [round(c[0], p), round(c[1], p)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]

    return {"type": geom["type"], "coordinates": rnd(geom["coordinates"])}


def leaflet_css() -> str:
    """CSS Leaflet с иконкой переключателя слоёв, встроенной как data URI."""
    import base64

    css = (VENDOR / "leaflet.css").read_text()
    for name in ["layers-2x.png", "layers.png"]:
        b64 = base64.b64encode((VENDOR / name).read_bytes()).decode()
        css = css.replace(f"images/{name}", f"data:image/png;base64,{b64}")
    return css


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-o", "--output", type=Path, default=config.DASHBOARD_PATH)
    args = parser.parse_args()
    R = config.RESULTS_DIR

    summary = json.loads((R / "summary.json").read_text(encoding="utf-8"))
    blocks = gpd.read_file(R / "blocks.geojson")
    blocks["land_use"] = blocks["land_use"].map(LAND_USE_RU)
    blocks["strelka_morphotype"] = blocks["strelka_morphotype"].map(STRELKA_RU)
    blocks["spacematrix_morphotype"] = blocks["spacematrix_morphotype"].map(spacematrix_ru)

    schools = gpd.read_file(R / "schools.geojson")
    links = gpd.read_file(R / "provision_links.geojson")
    okn = gpd.read_file(R / "heritage_points.geojson")
    zones = gpd.read_file(R / "heritage_protection_zones.geojson")
    stops = gpd.read_file(R / "transport_stops.geojson")
    boundary = gpd.read_file(R / "boundary.geojson")

    data = {
        "summary": summary,
        "built": date.today().isoformat(),
        "blocks": to_features(blocks, BLOCK_FIELDS),
        "schools": to_features(schools, {"name": ("name", None), "capacity": ("cap", 0),
                                         "capacity_is_estimated": ("est", None)}),
        "links": to_features(links, {"source": ("s", 0), "target": ("t", 0), "value": ("v", 0)}),
        "okn": to_features(okn, {"NAME": ("name", None), "ADDRESS": ("addr", None), "Category": ("cat", None),
                                 "semantic_type": ("type", None), "UNESCO": ("unesco", None),
                                 "REG_NUMBER": ("reg", None)}),
        "zones": to_features(zones, {"ZONE_DESC": ("desc", None), "OBJECTNAME": ("obj", None)}, precision=5),
        "stops": to_features(stops, {"name": ("name", None), "kind": ("kind", None), "source": ("src", None)}),
        "boundary": to_features(boundary, {"name": ("name", None)}),
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__LEAFLET_CSS__*/", leaflet_css()).replace("/*__LEAFLET_JS__*/", (VENDOR / "leaflet.js").read_text())
    html = html.replace("/*__DATA__*/null", payload.replace("</", "<\\/"))
    args.output.write_text(html, encoding="utf-8")
    print(f"Готово: {args.output} ({args.output.stat().st_size / 1e6:.1f} МБ, кварталов: {len(blocks)})")


if __name__ == "__main__":
    main()
