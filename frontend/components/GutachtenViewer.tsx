"use client";

import {
  Car,
  FileText,
  Gauge,
  Ruler,
  Settings2,
  Wrench,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import type { Gutachten } from "@/types";

function DataRow({
  label,
  value,
  mono,
  verified,
}: {
  label: string;
  value: string | number | boolean | null | undefined;
  mono?: boolean;
  verified?: boolean;
}) {
  if (value === null || value === undefined) {
    return (
      <div className="flex justify-between items-start gap-4 py-2 border-b border-slate-100 last:border-0">
        <span className="text-xs text-slate-500 shrink-0">{label}</span>
        <span className="text-sm text-slate-400 font-medium">—</span>
      </div>
    );
  }
  const display =
    typeof value === "boolean" ? (value ? "Yes" : "No") : String(value);
  return (
    <div className="flex justify-between items-start gap-4 py-2 border-b border-slate-100 last:border-0">
      <span className="text-xs text-slate-500 shrink-0">{label}</span>
      <div className="flex items-center gap-2">
        {verified === true && (
          <CheckCircle2 className="w-4 h-4 text-emerald-500" title="Verified exact match in document" />
        )}
        {verified === false && (
          <AlertCircle className="w-4 h-4 text-amber-500" title="Not found exactly in document" />
        )}
        <span
          className={`text-sm text-slate-800 text-right ${mono ? "font-mono" : "font-medium"}`}
        >
          {display}
        </span>
      </div>
    </div>
  );
}

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof Car;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 bg-slate-50 border-b border-slate-200">
        <Icon className="w-4 h-4 text-brand-600" />
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      </div>
      <div className="px-4 py-2">{children}</div>
    </div>
  );
}

interface GutachtenViewerProps {
  gutachten: Gutachten;
}

export function GutachtenViewer({ gutachten }: GutachtenViewerProps) {
  const { vehicle: v, modification: m } = gutachten;
  const wheels = m.wheels_front;

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-brand-50 rounded-lg">
            <FileText className="w-5 h-5 text-brand-600" />
          </div>
          <div>
            <p className="text-xs font-medium text-brand-600 uppercase tracking-wide">
              Ingested Gutachten
            </p>
            <h2 className="text-lg font-bold text-slate-900 mt-0.5">
              {gutachten.title}
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              {gutachten.issuing_authority} · {gutachten.issue_date}
            </p>
          </div>
        </div>
        {gutachten.notes && (
          <p className="mt-3 text-sm text-slate-600 bg-slate-50 rounded-lg p-3 border border-slate-100">
            {gutachten.notes}
          </p>
        )}
      </div>

      <Section title="Vehicle Data" icon={Car}>
        <DataRow
          label="Vehicle"
          value={`${v.make} ${v.model} ${v.variant}`}
          verified={gutachten.field_verifications?.['vehicle.make']}
        />
        <DataRow label="Chassis" value={v.chassis_code} mono verified={gutachten.field_verifications?.['vehicle.chassis_code']} />
        <DataRow label="VIN" value={v.vin} mono verified={gutachten.field_verifications?.['vehicle.vin']} />
        <DataRow label="First Registration" value={v.first_registration} verified={gutachten.field_verifications?.['vehicle.first_registration']} />
        <DataRow label="Fuel Type" value={v.fuel_type} verified={gutachten.field_verifications?.['vehicle.fuel_type']} />
        <DataRow label="Power" value={`${v.power_kw} kW`} verified={gutachten.field_verifications?.['vehicle.power_kw']} />
        <DataRow label="GVW" value={`${v.gross_vehicle_weight_kg} kg`} verified={gutachten.field_verifications?.['vehicle.gross_vehicle_weight_kg']} />
        <DataRow label="ESP" value={v.has_esp} verified={gutachten.field_verifications?.['vehicle.has_esp']} />
      </Section>

      {wheels && (
        <Section title="Wheel & Tire Specification" icon={Settings2}>
          <DataRow
            label="Rim"
            value={`${wheels.manufacturer} ${wheels.model}`}
            verified={gutachten.field_verifications?.['modification.wheels_front.manufacturer']}
          />
          <DataRow label="Tire Size" value={wheels.size} mono verified={gutachten.field_verifications?.['modification.wheels_front.size']} />
          <DataRow
            label="Rim Dimensions"
            value={`${wheels.rim_width_inch}J × ${wheels.rim_diameter_inch}″`}
            verified={gutachten.field_verifications?.['modification.wheels_front.rim_diameter_inch']}
          />
          <DataRow label="Offset (ET)" value={`ET${wheels.offset_et}`} mono verified={gutachten.field_verifications?.['modification.wheels_front.offset_et']} />
          <DataRow
            label="Load / Speed Index"
            value={`${wheels.load_index} / ${wheels.speed_index}`}
            mono
            verified={gutachten.field_verifications?.['modification.wheels_front.load_index']}
          />
          {wheels.abe_number && (
            <DataRow label="ABE Number" value={wheels.abe_number} mono verified={gutachten.field_verifications?.['modification.wheels_front.abe_number']} />
          )}
          {wheels.teilegutachten_number && (
            <DataRow
              label="Teilegutachten"
              value={wheels.teilegutachten_number}
              mono
              verified={gutachten.field_verifications?.['modification.wheels_front.teilegutachten_number']}
            />
          )}
        </Section>
      )}

      {(m.spacers_front_mm > 0 || m.spacers_rear_mm > 0) && (
        <Section title="Spacers" icon={Ruler}>
          <DataRow label="Front" value={`${m.spacers_front_mm} mm`} verified={gutachten.field_verifications?.['modification.spacers_front_mm']} />
          <DataRow label="Rear" value={`${m.spacers_rear_mm} mm`} verified={gutachten.field_verifications?.['modification.spacers_rear_mm']} />
          {m.spacer_spec && (
            <>
              <DataRow
                label="Hub-Centric"
                value={m.spacer_spec.hubcentric}
                verified={gutachten.field_verifications?.['modification.spacer_spec.hubcentric']}
              />
              <DataRow label="Material" value={m.spacer_spec.material} verified={gutachten.field_verifications?.['modification.spacer_spec.material']} />
            </>
          )}
          <DataRow
            label="Track Width Increase"
            value={`${m.total_track_width_increase_mm} mm`}
            verified={gutachten.field_verifications?.['modification.total_track_width_increase_mm']}
          />
        </Section>
      )}

      {m.lowering && (
        <Section title="Lowering" icon={Gauge}>
          <DataRow label="Spring Set" value={m.lowering.spring_set} verified={gutachten.field_verifications?.['modification.lowering.spring_set']} />
          <DataRow label="Drop Front" value={`−${m.lowering.drop_front_mm} mm`} verified={gutachten.field_verifications?.['modification.lowering.drop_front_mm']} />
          <DataRow label="Drop Rear" value={`−${m.lowering.drop_rear_mm} mm`} verified={gutachten.field_verifications?.['modification.lowering.drop_rear_mm']} />
          {m.lowering.teilegutachten_number && (
            <DataRow
              label="Teilegutachten"
              value={m.lowering.teilegutachten_number}
              mono
              verified={gutachten.field_verifications?.['modification.lowering.teilegutachten_number']}
            />
          )}
        </Section>
      )}

      <Section title="Original Equipment" icon={Wrench}>
        <DataRow label="OE Tire Front" value={v.original_tire_size_front} mono verified={gutachten.field_verifications?.['vehicle.original_tire_size_front']} />
        <DataRow label="OE Tire Rear" value={v.original_tire_size_rear} mono verified={gutachten.field_verifications?.['vehicle.original_tire_size_rear']} />
        <DataRow label="OE Rim Front" value={v.original_rim_size_front} mono verified={gutachten.field_verifications?.['vehicle.original_rim_size_front']} />
        <DataRow label="OE Rim Rear" value={v.original_rim_size_rear} mono verified={gutachten.field_verifications?.['vehicle.original_rim_size_rear']} />
        <DataRow
          label="OE Offset"
          value={`ET${v.original_offset_et_front} / ET${v.original_offset_et_rear}`}
          mono
          verified={gutachten.field_verifications?.['vehicle.original_offset_et_front']}
        />
      </Section>
    </div>
  );
}
