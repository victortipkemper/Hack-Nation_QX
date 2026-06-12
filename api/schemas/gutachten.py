from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class WheelTireSpec(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None  # e.g. "245/40 R19"
    rim_width_inch: Optional[float] = None
    rim_diameter_inch: Optional[float] = None
    offset_et: Optional[int] = None
    load_index: Optional[int] = None
    speed_index: Optional[str] = None
    abe_number: Optional[str] = None
    teilegutachten_number: Optional[str] = None


class SpacerSpec(BaseModel):
    thickness_mm: float
    hubcentric: bool
    material: str = "aluminium"


class LoweringSpec(BaseModel):
    spring_set: str
    drop_front_mm: float
    drop_rear_mm: float
    teilegutachten_number: Optional[str] = None


class ModificationData(BaseModel):
    modification_type: str  # "wheels_tires", "lowering", "combined"
    wheels_front: Optional[WheelTireSpec] = None
    wheels_rear: Optional[WheelTireSpec] = None
    spacers_front_mm: float = 0
    spacers_rear_mm: float = 0
    spacer_spec: Optional[SpacerSpec] = None
    lowering: Optional[LoweringSpec] = None
    total_track_width_increase_mm: float = 0


class VehicleData(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    chassis_code: Optional[str] = None
    vin: Optional[str] = None
    first_registration: Optional[date] = None
    fuel_type: Optional[str] = None  # "petrol", "diesel", "electric", "hybrid"
    power_kw: Optional[int] = None
    original_tire_size_front: Optional[str] = None
    original_tire_size_rear: Optional[str] = None
    original_rim_size_front: Optional[str] = None
    original_rim_size_rear: Optional[str] = None
    original_offset_et_front: Optional[int] = None
    original_offset_et_rear: Optional[int] = None
    has_esp: Optional[bool] = None
    has_abs: Optional[bool] = None
    gross_vehicle_weight_kg: Optional[int] = None
    max_rear_axle_load_kg: Optional[int] = None


class Gutachten(BaseModel):
    gutachten_id: str
    gutachten_type: str  # "standard_abe", "teilegutachten", "lowering", "ev_edge", "flawed"
    title: str
    issuing_authority: str
    issue_date: date
    vehicle: VehicleData
    modification: ModificationData
    notes: Optional[str] = None
    field_verifications: dict[str, bool] = Field(default_factory=dict)


class CaseSummary(BaseModel):
    id: str
    gutachten_type: str
    title: str
    description: str
    expected_verdict: str
    vehicle_summary: str
