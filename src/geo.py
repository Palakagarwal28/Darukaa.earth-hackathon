"""Geo → ecoregion inference (offline, bonus requirement). India-focused + generic fallback."""
from typing import Dict, Any, Optional, List

# coarse bounding boxes: (lat_min, lat_max, lon_min, lon_max) -> region
BOXES = [
    ((8, 15, 74, 80), {"region": "semi-arid", "note": "Deccan plateau: low erratic rainfall"}),
    ((22, 30, 68, 75), {"region": "arid", "note": "Thar fringe: very low rainfall, sandy soils"}),
    ((21, 27, 75, 82), {"region": "semi-arid", "note": "Central India: vertisols, monsoon-dependent"}),
    ((8, 12, 75, 78), {"region": "humid", "note": "Western Ghats: high biodiversity, high rainfall"}),
    ((26, 32, 88, 95), {"region": "humid", "note": "NE India: high rainfall, forest fragments"}),
]

def infer_region(lat: float, lon: float) -> Dict[str, Any]:
    for (la0, la1, lo0, lo1), info in BOXES:
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return {"region": info["region"], "geo_note": info["note"], "geo": [lat, lon]}
    # generic global fallback by latitude
    if abs(lat) < 15:
        return {"region": "humid", "geo_note": "Tropical belt assumption", "geo": [lat, lon]}
    if abs(lat) > 35:
        return {"region": "temperate", "geo_note": "Mid-latitude assumption", "geo": [lat, lon]}
    return {"region": "semi-arid", "geo_note": "Subtropical default — confirm locally", "geo": [lat, lon]}

def apply_geo(site: Dict[str, Any]) -> Dict[str, Any]:
    site = dict(site)
    g = site.get("geo")
    if isinstance(g, (list, tuple)) and len(g) == 2 and not site.get("region"):
        try:
            site.update(infer_region(float(g[0]), float(g[1])))
        except Exception:
            pass
    return site
