export interface WheelTireSpec {
  manufacturer: string;
  model: string;
  size: string;
  rim_width_inch: number;
  rim_diameter_inch: number;
  offset_et: number;
  load_index: number;
  speed_index: string;
  abe_number?: string | null;
  teilegutachten_number?: string | null;
}

export interface SpacerSpec {
  thickness_mm: number;
  hubcentric: boolean;
  material: string;
}

export interface LoweringSpec {
  spring_set: string;
  drop_front_mm: number;
  drop_rear_mm: number;
  teilegutachten_number?: string | null;
}

export interface ModificationData {
  modification_type: string;
  wheels_front?: WheelTireSpec | null;
  wheels_rear?: WheelTireSpec | null;
  spacers_front_mm: number;
  spacers_rear_mm: number;
  spacer_spec?: SpacerSpec | null;
  lowering?: LoweringSpec | null;
  total_track_width_increase_mm: number;
}

export interface VehicleData {
  make: string;
  model: string;
  variant: string;
  chassis_code: string;
  vin: string;
  first_registration: string;
  fuel_type: string;
  power_kw: number;
  original_tire_size_front: string;
  original_tire_size_rear: string;
  original_rim_size_front: string;
  original_rim_size_rear: string;
  original_offset_et_front: number;
  original_offset_et_rear: number;
  has_esp: boolean;
  has_abs: boolean;
  gross_vehicle_weight_kg: number;
}

export interface Gutachten {
  gutachten_id: string;
  gutachten_type: string;
  title: string;
  issuing_authority: string;
  issue_date: string;
  vehicle: VehicleData;
  modification: ModificationData;
  notes?: string | null;
}

export interface CaseSummary {
  id: string;
  gutachten_type: string;
  title: string;
  description: string;
  expected_verdict: string;
  vehicle_summary: string;
}

export interface RuleResult {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  flagged: boolean;
  citation: string;
  reason: string;
}

export interface LevelResult {
  level: number;
  level_name: string;
  rules: RuleResult[];
  all_passed: boolean;
  any_flagged: boolean;
}

export type VerdictStatus = "PASS" | "FAIL" | "AUDIT_FLAGGED";

export interface FinalVerdict {
  status: VerdictStatus;
  summary: string;
  deterministic: boolean;
  audit_trail_id: string;
}

export interface TestPlanResult {
  gutachten_id: string;
  levels: LevelResult[];
  final_verdict: FinalVerdict;
  executed_at: string;
}
