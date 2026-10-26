import { cn } from "@/lib/utils";
import type { LeakStatus, Severity, DeviceStatus } from "@/lib/types";

const severityStyles: Record<Severity, string> = {
  critical: "bg-destructive/12 text-destructive border-destructive/30",
  high: "bg-warning/15 text-warning border-warning/35",
  medium: "bg-primary/12 text-primary border-primary/30",
  low: "bg-success/12 text-success border-success/30",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold capitalize",
        severityStyles[severity],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
}

const statusStyles: Record<LeakStatus, string> = {
  active: "bg-destructive/12 text-destructive border-destructive/30",
  investigating: "bg-warning/15 text-warning border-warning/35",
  resolved: "bg-success/12 text-success border-success/30",
};

export function StatusBadge({ status }: { status: LeakStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
        statusStyles[status],
      )}
    >
      {status}
    </span>
  );
}

const deviceStyles: Record<DeviceStatus, string> = {
  online: "bg-success/12 text-success border-success/30",
  offline: "bg-destructive/12 text-destructive border-destructive/30",
  maintenance: "bg-warning/15 text-warning border-warning/35",
};

export function DeviceStatusBadge({ status }: { status: DeviceStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize",
        deviceStyles[status],
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

export function LiveIndicator({ label = "Live", className }: { label?: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs font-semibold text-success",
        className,
      )}
    >
      <span className="pulse-ring size-2 rounded-full bg-success text-success" />
      {label}
    </span>
  );
}
