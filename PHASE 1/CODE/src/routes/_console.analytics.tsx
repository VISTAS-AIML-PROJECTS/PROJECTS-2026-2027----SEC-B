import { createFileRoute } from "@tanstack/react-router";
import { Droplets, Gauge, Timer, TrendingUp } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState } from "@/components/empty-state";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLeaks, useReadings, weeklyCounts, zoneCounts } from "@/lib/queries";

export const Route = createFileRoute("/_console/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics — AquaSense" },
      { name: "description", content: "Detection trends, zone comparisons and water loss analytics computed from your leak records." },
      { property: "og:title", content: "Analytics — AquaSense" },
      { property: "og:description", content: "Leak detection analytics and acoustic trends." },
    ],
  }),
  component: Analytics,
});

function Analytics() {
  const { data: leaks = [] } = useLeaks();
  const { data: readings = [] } = useReadings(60);

  const weekly = weeklyCounts(leaks);
  const zones = zoneCounts(leaks).sort((a, b) => b.leaks - a.leaks);
  const resolved = leaks.filter((l) => l.status === "resolved");
  const totalLoss = leaks.reduce((s, l) => s + Number(l.estimated_loss_lpm), 0);
  const recovered = resolved.reduce((s, l) => s + Number(l.estimated_loss_lpm), 0);
  const avgConfidence = leaks.length
    ? leaks.reduce((s, l) => s + Number(l.confidence), 0) / leaks.length
    : 0;
  const acoustic = readings.map((r) => ({
    t: new Date(r.recorded_at).toLocaleTimeString(),
    level: Number(r.acoustic_db),
  }));

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Everything below is calculated from your recorded leak events and sensor readings." />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Leaks detected" value={String(leaks.length)} hint="all recorded events" icon={TrendingUp} />
        <KpiCard label="Resolved" value={String(resolved.length)} hint="closed by field teams" icon={Timer} tone="success" />
        <KpiCard label="Loss recovered" value={`${recovered.toFixed(0)} L/min`} hint={`of ${totalLoss.toFixed(0)} L/min detected`} icon={Droplets} tone="primary" />
        <KpiCard label="Avg. confidence" value={`${avgConfidence.toFixed(1)}%`} hint="detection confidence" icon={Gauge} tone="warning" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Detections vs resolutions</CardTitle>
            <CardDescription>Grouped by week of detection</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {weekly.length === 0 ? (
              <EmptyState title="No leak events yet" description="Charts fill in as leak events are recorded." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="week" stroke="var(--muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                  <Legend />
                  <Bar dataKey="leaks" name="Detected" fill="var(--primary)" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="resolved" name="Resolved" fill="var(--accent)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Estimated loss per week</CardTitle>
            <CardDescription>Litres per minute across detected leaks</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {weekly.length === 0 ? (
              <EmptyState title="No loss data yet" description="Loss trends appear once leaks are recorded." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="week" stroke="var(--muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                  <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                  <Line type="monotone" dataKey="loss" name="Loss (L/min)" stroke="var(--success)" strokeWidth={3} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Zone risk ranking</CardTitle>
          <CardDescription>Leak events per zone</CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          {zones.length === 0 ? (
            <EmptyState title="No zone data yet" description="Zone rankings build from recorded leak events." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zones} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" stroke="var(--muted-foreground)" fontSize={11} allowDecimals={false} />
                <YAxis dataKey="zone" type="category" stroke="var(--muted-foreground)" fontSize={11} width={90} />
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                <Bar dataKey="leaks" fill="var(--chart-2)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Acoustic level profile</CardTitle>
          <CardDescription>Most recent recorded sensor samples</CardDescription>
        </CardHeader>
        <CardContent className="h-72">
          {acoustic.length === 0 ? (
            <EmptyState title="No sensor readings yet" description="Acoustic profiles appear once your nodes record samples." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={acoustic}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="t" stroke="var(--muted-foreground)" fontSize={11} />
                <YAxis stroke="var(--muted-foreground)" fontSize={11} unit="dB" />
                <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                <Line type="monotone" dataKey="level" name="Acoustic level" stroke="var(--primary)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
