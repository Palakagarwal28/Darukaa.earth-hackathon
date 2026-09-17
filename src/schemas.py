"""Validated site + response schemas. All 5 knowledge domains covered."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class SiteInput(BaseModel):
    # soil
    soc_pct: Optional[float] = Field(default=None, ge=0, le=15, description="Soil organic carbon %")
    soil_ph: Optional[float] = Field(default=None, ge=0, le=14)
    soil_moisture: Optional[str] = None  # low/medium/high
    # land
    land_use: Optional[str] = None  # monoculture, grassland, forest, degraded...
    crop: Optional[str] = None
    # biodiversity
    species_richness: Optional[str] = None
    habitat_diversity: Optional[str] = None
    # climate
    rainfall: Optional[str] = None  # low/medium/high
    rainfall_mm: Optional[float] = Field(default=None, ge=0, le=5000)
    temperature_c: Optional[float] = None
    region: Optional[str] = None  # semi-arid, arid, humid...
    # human impact
    pollution: Optional[str] = None
    pesticide_use: Optional[bool] = None
    deforestation: Optional[bool] = None
    burning: Optional[bool] = None
    # bonus geo
    geo: Optional[List[float]] = None  # [lat, lon]
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}

class ChatIn(BaseModel):
    session_id: str = "demo"
    message: str = Field(min_length=1)
    site_json: Optional[SiteInput] = None
    enrich: bool = True
    verbalize: bool = False

class AssessIn(BaseModel):
    site: SiteInput
    query: str = ""
    enrich: bool = True
    verbalize: bool = False

class Recommendation(BaseModel):
    recommendation: str
    why_it_works: str
    metrics_improved: List[str]
    expected_effect: str
    time_horizon: str
    confidence: str
    confidence_score: float
    reference: str
    kb_id: str
    retrieval_score: float
