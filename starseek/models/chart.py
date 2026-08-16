from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .enums import (
    Planet, Sign, AspectType, Dignity, HouseQuality,
    HouseSystem, Element, Modality,
)


class PlanetPosition(BaseModel):
    planet: Planet
    longitude: float = Field(..., description="Ecliptic longitude in degrees (0-360)")
    latitude: float = Field(..., description="Ecliptic latitude in degrees")
    speed: float = Field(..., description="Daily motion in degrees/day")
    is_retrograde: bool = Field(..., description="Whether the planet is in retrograde motion")
    sign: Sign = Field(..., description="Zodiac sign the planet occupies")
    sign_degree: float = Field(..., description="Degree within the sign (0-30)")
    sign_minute: int = Field(..., description="Arc-minute within the degree (0-59)")
    house: int = Field(..., ge=1, le=12, description="House number the planet falls in")
    dignity: Optional[Dignity] = Field(None, description="Essential dignity, if any")


class HouseCusp(BaseModel):
    house_number: int = Field(..., ge=1, le=12)
    longitude: float = Field(..., description="Ecliptic longitude of house cusp")
    sign: Sign = Field(..., description="Sign on the cusp")
    sign_degree: float = Field(..., description="Degree within the sign")
    quality: HouseQuality = Field(..., description="Angular, succedent, or cadent")


class Aspect(BaseModel):
    planet_a: Planet
    planet_b: Planet
    aspect_type: AspectType
    exact_angle: float = Field(..., description="The exact angle between the two bodies")
    orb: float = Field(..., description="How far from exact the aspect is (in degrees)")
    is_applying: bool = Field(..., description="Whether the aspect is applying or separating")


class ChartSummary(BaseModel):
    dominant_element: Element
    element_counts: dict[Element, int]
    dominant_modality: Modality
    modality_counts: dict[Modality, int]
    stelliums: list[dict] = Field(default_factory=list, description="Groups of 3+ planets in the same sign")


class BirthChart(BaseModel):
    id: Optional[int] = Field(None, description="Database ID if persisted")
    name: Optional[str] = None
    birth_datetime: datetime
    birth_location: str = Field(..., description="Resolved city/location name")
    latitude: float
    longitude: float
    timezone: str
    house_system: HouseSystem

    planets: list[PlanetPosition]
    houses: list[HouseCusp]
    aspects: list[Aspect]
    summary: ChartSummary

    computed_at: datetime = Field(..., description="When this chart was computed")


class TransitPosition(BaseModel):
    planet: Planet
    longitude: float = Field(..., description="Ecliptic longitude in degrees (0-360)")
    latitude: float = Field(..., description="Ecliptic latitude in degrees")
    speed: float = Field(..., description="Daily motion in degrees/day")
    is_retrograde: bool = Field(..., description="Whether the planet is in retrograde motion")
    sign: Sign = Field(..., description="Zodiac sign the planet occupies")
    sign_degree: float = Field(..., description="Degree within the sign (0-30)")
    sign_minute: int = Field(..., description="Arc-minute within the degree (0-59)")
    natal_house: int = Field(..., ge=1, le=12, description="Natal house the transiting planet falls in")


class TransitAspect(BaseModel):
    transit_planet: Planet = Field(..., description="The transiting planet")
    natal_planet: Planet = Field(..., description="The natal planet being aspected")
    aspect_type: AspectType
    exact_angle: float = Field(..., description="The exact angle between the two bodies")
    orb: float = Field(..., description="How far from exact the aspect is (in degrees)")
    is_applying: bool = Field(..., description="Whether the aspect is applying or separating")


class TransitReport(BaseModel):
    natal_chart_id: Optional[int] = Field(None, description="ID of the natal chart")
    natal_name: Optional[str] = Field(None, description="Name from the natal chart")
    transit_datetime: datetime = Field(..., description="Date/time for the transit calculation")
    transit_positions: list[TransitPosition]
    transit_aspects: list[TransitAspect]
    computed_at: datetime = Field(..., description="When this report was computed")
