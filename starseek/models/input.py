from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional

from .enums import HouseSystem


class BirthData(BaseModel):
    name: Optional[str] = Field(None, description="Name of the person (optional, for labeling)")
    birth_datetime: datetime = Field(..., description="Date and time of birth (ISO 8601)")
    city: Optional[str] = Field(None, description="City of birth (triggers geocoding if provided)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Birth latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Birth longitude")
    timezone: Optional[str] = Field(None, description="IANA timezone (e.g., 'America/New_York')")
    house_system: HouseSystem = Field(HouseSystem.PLACIDUS, description="House system to use")

    @model_validator(mode="after")
    def validate_location(self) -> "BirthData":
        has_coords = self.latitude is not None and self.longitude is not None and self.timezone is not None
        has_city = self.city is not None
        if not has_coords and not has_city:
            raise ValueError("Either 'city' or ('latitude', 'longitude', 'timezone') must be provided")
        return self
