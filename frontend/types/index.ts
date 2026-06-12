export interface WheelTireSpec {
  manufacturer?: string | null;
  model?: string | null;
  size?: string | null;
  rim_width_inch?: number | null;
  rim_diameter_inch?: number | null;
  offset_et?: number | null;
  load_index?: number | null;
  speed_index?: string | null;
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
  make?: string | null;
  model?: string | null;
  variant?: string | null;
  chassis_code?: string | null;
  vin?: string | null;
  first_registration?: string | null;
  fuel_type?: string | null;
  power_kw?: number | null;
  original_tire_size_front?: string | null;
  original_tire_size_rear?: string | null;
  original_rim_size_front?: string | null;
  original_rim_size_rear?: string | null;
  original_offset_et_front?: number | null;
  original_offset_et_rear?: number | null;
  has_esp?: boolean | null;
  has_abs?: boolean | null;
  gross_vehicle_weight_kg?: number | null;
  max_rear_axle_load_kg?: number | null;
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
  field_verifications?: Record<string, boolean>;
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

export interface HighlightRegion {
  page: number;
  top: number;
  left: number;
  width: number;
  height: number;
  label?: string | null;
}

export interface RegulatoryLink {
  label: string;
  url: string;
}

export interface RuleAnnotation {
  rule_id: string;
  paragraph_ref?: string;
  highlight_section_id: string;
  highlight_text: string;
  ai_explanation: string;
  regulatory_references?: string[];
  regulatory_links?: RegulatoryLink[];
  remediation_hint?: string;
  regions?: HighlightRegion[];
}

export interface DocumentSection {
  id: string;
  label: string;
  content: string;
  page?: number | null;
}

export interface UploadedDocument {
  upload_id: string;
  filename: string;
  pdf_url: string;
  page_count: number;
  page_urls: string[];
  sections: DocumentSection[];
  annotations: RuleAnnotation[];
}

export interface WhiteBoxStep {
  step: number;
  check_id: string;
  level: number;
  check_name: string;
  citation: string;
  /** error = Beanstandung; advisory = nur Hinweis (z. B. EV, ESP) */
  severity?: "error" | "advisory";
  applicable: boolean;
  applicability_reason: string;
  executed: boolean;
  passed?: boolean | null;
  flagged: boolean;
  skipped_reason?: string | null;
  evidence: string;
  reason: string;
  remediation_hint: string;
  /** Procedural verification steps — learned from corpus, no doc references */
  verification_hint?: string;
  exemplar_reference: string;
  /** seed | corpus+seed | corpus-primary */
  hint_source?: string;
  review_fingerprint?: string;
  expert_override?: boolean;
  expert_override_id?: string;
  expert_confirmed?: boolean;
  expert_confirmed_id?: string;
}

export interface ExpertReviewRequest {
  check_id: string;
  check_name?: string;
  evidence: string;
  decision: "approve" | "reject";
  note?: string;
  gutachten_id?: string;
  expert?: string;
}

export interface ExpertKnowledgeEntry {
  entry_id: string;
  fingerprint: string;
  decision?: "approve" | "reject";
  check_id: string;
  check_name?: string;
  evidence: string;
  note?: string;
  gutachten_id?: string;
  expert?: string;
  created_at: string;
}

export interface ExpertReviewResponse {
  decision: string;
  stored: boolean;
  entry?: ExpertKnowledgeEntry | null;
}

export interface ChecklistExecution {
  gutachten_id: string;
  checklist_version: string;
  total_checks: number;
  applicable_checks: number;
  executed_checks: number;
  steps: WhiteBoxStep[];
  levels: LevelResult[];
  final_verdict: FinalVerdict;
  executed_at: string;
}

export interface CorpusCase {
  case_id: string;
  filename: string;
  path: string;
  expected_verdict: string;
  expected_gap?: string | null;
}

export interface UploadResponse {
  upload_id: string;
  gutachten: Gutachten;
  test_plan: TestPlanResult;
  checklist_execution?: ChecklistExecution | null;
  document: UploadedDocument;
  bundle_manifest?: Record<string, unknown> | null;
}
