import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  delta?: number;
  icon: LucideIcon;
  tone?: "primary" | "success" | "warning" | "destructive";
  className?: string;
}

const tones = {
  primary: "bg-primary/10 text-primary",
  success: "bg-success/12 text-success",
  warning: "bg-warning/15 text-warning",
  destructive: "bg-destructive/12 text-destructive",
};

export function KpiCard({
  label,
  value,
  hint,
  delta,
  icon: Icon,
  tone = "primary",
  className,
}: KpiCardProps) {
  const positive = (delta ?? 0) >= 0;
  return (
    <Card className={cn("card-hover animate-fade-up overflow-hidden border-border/70", className)}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {label}
            </p>
            <p className="mt-2 font-display text-3xl font-semibold tracking-tight">{value}</p>
          </div>
          <span className={cn("grid size-11 place-items-center rounded-xl", tones[tone])}>
            <Icon className="size-5" />
          </span>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
          {delta !== undefined && (
            <span
              className={cn(
                "inline-flex items-center gap-1 font-semibold",
                positive ? "text-success" : "text-destructive",
              )}
            >
              {positive ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
              {Math.abs(delta)}%
            </span>
          )}
          {hint && <span>{hint}</span>}
        </div>
      </CardContent>
    </Card>
  );
}
