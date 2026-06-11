import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { VerdictStatus } from "@/types";

const config: Record<
  VerdictStatus,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  PASS: {
    label: "PASS",
    icon: CheckCircle2,
    className: "bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-100",
  },
  FAIL: {
    label: "FAIL",
    icon: XCircle,
    className: "bg-red-50 text-red-700 border-red-200 ring-red-100",
  },
  AUDIT_FLAGGED: {
    label: "AUDIT FLAGGED",
    icon: AlertTriangle,
    className: "bg-amber-50 text-amber-700 border-amber-200 ring-amber-100",
  },
};

interface VerdictBadgeProps {
  status: VerdictStatus;
  size?: "sm" | "lg";
}

export function VerdictBadge({ status, size = "lg" }: VerdictBadgeProps) {
  const { label, icon: Icon, className } = config[status];
  const sizeClass =
    size === "lg"
      ? "px-6 py-3 text-xl gap-3"
      : "px-2.5 py-1 text-xs gap-1.5";

  return (
    <div
      className={`inline-flex items-center font-bold border rounded-xl ring-4 ${className} ${sizeClass}`}
    >
      <Icon className={size === "lg" ? "w-7 h-7" : "w-3.5 h-3.5"} />
      {label}
    </div>
  );
}
