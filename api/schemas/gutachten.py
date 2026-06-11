from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class WheelTireSpec(BaseModel):
    manufacturer: str
    model: str
    size: str  # e.g. "245/40 R19"
    rim_width_inch: float
    rim_diameter_inch: float
    offset_et: int
    load_index: int
    speed_index: str
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
    make: str
    model: str
    variant: str
    chassis_code: str
    vin: str
    first_registration: date
    fuel_type: str  # "petrol", "diesel", "electric", "hybrid"
    power_kw: int
    original_tire_size_front: str
    original_tire_size_rear: str
    original_rim_size_front: str
    original_rim_size_rear: str
    original_offset_et_front: int
    original_offset_et_rear: int
    has_esp: bool = True
    has_abs: bool = True
    gross_vehicle_weight_kg: int
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


class CaseSummary(BaseModel):
    id: str
    gutachten_type: str
    title: str
    description: str
    expected_verdict: str
    vehicle_summary: str
