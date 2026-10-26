import { createFileRoute, Link } from "@tanstack/react-router";
import { Activity, Droplets, Gauge, Radio, TriangleAlert } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState } from "@/components/empty-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { DeviceStatusBadge, LiveIndicator, SeverityBadge, StatusBadge } from "@/components/severity-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { severityCounts, useDevices, useLeaks, zoneCounts } from "@/lib/queries";

export const Route = createFileRoute("/_console/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — AquaSense Leak Monitoring" },
      { name: "description", content: "KPI overview of active leaks, sensor health and water loss across all pipeline zones." },
      { property: "og:title", content: "Dashboard — AquaSense Leak Monitoring" },
      { property: "og:description", content: "Live KPIs for acoustic leak detection across municipal pipeline zones." },
    ],
  }),
  component: Dashboard,
});

const severityColors = ["var(--destructive)", "var(--warning)", "var(--primary)", "var(--success)"];

function Dashboard() {
  const { data: devices = [] } = useDevices();
  const { data: leaks = [] } = useLeaks();

  const active = leaks.filter((l) => l.status !== "resolved");
  const online = devices.filter((d) => d.status === "online").length;
  const resolved = leaks.filter((l) => l.status === "resolved");
  const litresRecovered = resolved.reduce((sum, l) => sum + Number(l.estimated_loss_lpm), 0);
  const avgConfidence = leaks.length
    ? leaks.reduce((s, l) => s + Number(l.confidence), 0) / leaks.length
    : 0;
  const zones = zoneCounts(leaks);
  const severities = severityCounts(leaks);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operations dashboard"
        description="Network-wide acoustic leak detection overview from your live records."
        actions={<LiveIndicator />}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Active leaks" value={String(active.length)} hint="awaiting field action" icon={TriangleAlert} tone="destructive" />
        <KpiCard label="Devices online" value={`${online}/${devices.length}`} hint="registered sensor nodes" icon={Gauge} tone="success" />
        <KpiCard label="Loss recovered" value={`${litresRecovered.toFixed(0)} L/min`} hint="from resolved leaks" icon={Droplets} tone="primary" />
        <KpiCard label="Avg. confidence" value={`${avgConfidence.toFixed(1)}%`} hint="across recorded events" icon={Activity} tone="warning" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/70 lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle className="font-display text-lg">Live leak status</CardTitle>
              <CardDescription>Events requiring field action</CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/history">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {active.length === 0 ? (
              <EmptyState
                icon={TriangleAlert}
                title="No leak events yet"
                description="Recorded leak events will appear here as soon as your sensors report them."
              />
            ) : (
              active.map((leak) => (
                <div
                  key={leak.id}
                  className="card-hover flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 p-4"
                >
                  <div className="min-w-0">
                    <p className="font-medium">
                      {leak.reference} · {leak.devices?.name ?? "Unassigned device"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {leak.zone || leak.devices?.zone || "No zone"} · {Number(leak.acoustic_db)} dB ·{" "}
                      {Number(leak.frequency_hz)} Hz · {Number(leak.estimated_loss_lpm)} L/min
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={leak.severity} />
                    <StatusBadge status={leak.status} />
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Severity mix</CardTitle>
            <CardDescription>All recorded events</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {severities.length === 0 ? (
              <EmptyState title="Nothing to chart yet" description="Severity mix appears once leaks are recorded." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={severities} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}>
                    {severities.map((_, i) => (
                      <Cell key={i} fill={severityColors[i % severityColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Leaks by zone</CardTitle>
          <CardDescription>Totals from your leak records</CardDescription>
        </CardHeader>
        <CardContent className="h-64">
          {zones.length === 0 ? (
            <EmptyState title="No zone data yet" description="Zone totals build up from recorded leak events." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zones}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="zone" stroke="var(--muted-foreground)" fontSize={11} />
                <YAxis stroke="var(--muted-foreground)" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                <Bar dataKey="leaks" fill="var(--primary)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Sensor fleet health</CardTitle>
          <CardDescription>Battery and signal strength per acoustic node</CardDescription>
        </CardHeader>
        <CardContent className={devices.length ? "grid gap-4 sm:grid-cols-2 xl:grid-cols-4" : undefined}>
          {devices.length === 0 ? (
            <EmptyState
              icon={Radio}
              title="No devices registered"
              description="Register your acoustic sensor nodes in the admin panel to see fleet health."
              action={
                <Button size="sm" asChild>
                  <Link to="/admin">Go to admin panel</Link>
                </Button>
              }
            />
          ) : (
            devices.map((d) => (
              <div key={d.id} className="rounded-xl border border-border/70 p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{d.code}</p>
                  <DeviceStatusBadge status={d.status} />
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground">{d.zone || "No zone"}</p>
                <div className="mt-3 space-y-2">
                  <div>
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Battery</span>
                      <span>{d.battery}%</span>
                    </div>
                    <Progress value={d.battery} className="mt-1 h-1.5" />
                  </div>
                  <div>
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Signal</span>
                      <span>{d.signal}%</span>
                    </div>
                    <Progress value={d.signal} className="mt-1 h-1.5" />
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
