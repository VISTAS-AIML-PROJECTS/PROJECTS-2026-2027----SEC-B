import { createFileRoute } from "@tanstack/react-router";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDevices, useLeaks, weeklyCounts, zoneCounts } from "@/lib/queries";
import type { LeakEvent } from "@/lib/types";

export const Route = createFileRoute("/_console/reports")({
  head: () => ({
    meta: [
      { title: "Reports — AquaSense" },
      { name: "description", content: "Generate and download leak detection reports built from your own recorded events." },
      { property: "og:title", content: "Reports — AquaSense" },
      { property: "og:description", content: "On-demand leak detection reporting and exports." },
    ],
  }),
  component: ReportsPage,
});

function downloadCsv(filename: string, rows: string[][]) {
  const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function leakRows(leaks: LeakEvent[]) {
  return [
    ["Reference", "Device", "Zone", "Severity", "Status", "Confidence", "Loss (L/min)", "Detected"],
    ...leaks.map((l) => [
      l.reference,
      l.devices?.code ?? "",
      l.zone || l.devices?.zone || "",
      l.severity,
      l.status,
      String(l.confidence),
      String(l.estimated_loss_lpm),
      new Date(l.detected_at).toISOString(),
    ]),
  ];
}

function ReportsPage() {
  const { data: leaks = [] } = useLeaks();
  const { data: devices = [] } = useDevices();
  const weekly = weeklyCounts(leaks);
  const zones = zoneCounts(leaks);

  const exportLeaks = () => {
    if (leaks.length === 0) {
      toast.error("There is no leak data to report yet");
      return;
    }
    downloadCsv("aquasense-leak-report.csv", leakRows(leaks));
    toast.success("Leak report downloaded");
  };

  const exportDevices = () => {
    if (devices.length === 0) {
      toast.error("No devices registered yet");
      return;
    }
    downloadCsv("aquasense-device-report.csv", [
      ["Code", "Name", "Zone", "Pipeline", "Status", "Battery", "Signal", "Firmware", "Baseline dB"],
      ...devices.map((d) => [
        d.code,
        d.name,
        d.zone,
        d.pipeline,
        d.status,
        String(d.battery),
        String(d.signal),
        d.firmware,
        String(d.baseline_db),
      ]),
    ]);
    toast.success("Device report downloaded");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Reports are generated live from your recorded leak events and devices."
        actions={
          <>
            <Button variant="outline" onClick={() => window.print()}>
              <FileText className="mr-2 size-4" /> Print / PDF
            </Button>
            <Button onClick={exportLeaks}>
              <FileSpreadsheet className="mr-2 size-4" /> Export leak data
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        {weekly.length === 0 ? (
          <Card className="border-border/70 md:col-span-3">
            <CardContent className="p-6">
              <EmptyState
                title="No reporting periods yet"
                description="Weekly summaries appear as soon as leak events are recorded."
              />
            </CardContent>
          </Card>
        ) : (
          weekly.slice(-3).map((w) => (
            <Card key={w.week} className="card-hover border-border/70">
              <CardHeader>
                <CardTitle className="font-display text-lg">{w.week} summary</CardTitle>
                <CardDescription>
                  {w.leaks} leak{w.leaks === 1 ? "" : "s"} · {w.resolved} resolved
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p className="font-display text-2xl font-semibold text-foreground">
                  {w.loss.toFixed(0)} L/min detected
                </p>
                <Button variant="outline" size="sm" onClick={exportLeaks}>
                  <Download className="mr-2 size-4" /> Download data
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Sensor fleet report</CardTitle>
          <CardDescription>
            {devices.length} registered device{devices.length === 1 ? "" : "s"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={exportDevices}>
            <Download className="mr-2 size-4" /> Export device data
          </Button>
        </CardContent>
      </Card>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Zone breakdown</CardTitle>
          <CardDescription>Leak counts per zone</CardDescription>
        </CardHeader>
        <CardContent className={zones.length ? "grid gap-3 sm:grid-cols-3 lg:grid-cols-6" : undefined}>
          {zones.length === 0 ? (
            <EmptyState title="No zone data yet" description="Zone breakdowns build from recorded leak events." />
          ) : (
            zones.map((z) => (
              <div key={z.zone} className="rounded-xl border border-border/70 p-4 text-center">
                <p className="text-xs text-muted-foreground">{z.zone}</p>
                <p className="font-display text-2xl font-semibold">{z.leaks}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
