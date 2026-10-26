import { createFileRoute } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { useEffect } from "react";
import { Activity, Radio, Waves } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { DeviceStatusBadge, LiveIndicator, SeverityBadge } from "@/components/severity-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { useDevices, useLeaks, useReadings } from "@/lib/queries";
import { useQueryClient } from "@tanstack/react-query";

export const Route = createFileRoute("/_console/monitoring")({
  head: () => ({
    meta: [
      { title: "Real-Time Monitoring — AquaSense" },
      { name: "description", content: "Live acoustic waveform, decibel levels and threshold breach indicators for every sensor node." },
      { property: "og:title", content: "Real-Time Monitoring — AquaSense" },
      { property: "og:description", content: "Streaming acoustic telemetry from the pipeline sensor network." },
    ],
  }),
  component: Monitoring,
});

const THRESHOLD = 55;

function Monitoring() {
  const { data: devices = [] } = useDevices();
  const { data: leaks = [] } = useLeaks();
  const { data: readings = [] } = useReadings(40);
  const queryClient = useQueryClient();

  useEffect(() => {
    const channel = supabase
      .channel("sensor-readings-live")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "sensor_readings" }, () => {
        queryClient.invalidateQueries({ queryKey: ["sensor_readings"] });
      })
      .subscribe();
    return () => {
      supabase.removeChannel(channel);
    };
  }, [queryClient]);

  const stream = readings.map((r) => ({
    t: new Date(r.recorded_at).toLocaleTimeString(),
    level: Number(r.acoustic_db),
  }));
  const current = stream.length ? stream[stream.length - 1]!.level : null;
  const breach = current !== null && current > THRESHOLD;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Real-time monitoring"
        description="Acoustic samples recorded by your sensor network."
        actions={<LiveIndicator label={stream.length ? "Streaming" : "Waiting for data"} />}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/70 lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle className="font-display text-lg">Acoustic level stream</CardTitle>
              <CardDescription>Alert threshold {THRESHOLD} dB</CardDescription>
            </div>
            {current !== null && <Badge variant={breach ? "destructive" : "secondary"}>{current} dB</Badge>}
          </CardHeader>
          <CardContent className="h-72">
            {stream.length === 0 ? (
              <EmptyState
                icon={Waves}
                title="No acoustic readings yet"
                description="Readings from your sensor nodes appear here in real time as they arrive."
              />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stream}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="t" stroke="var(--muted-foreground)" fontSize={11} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={11} unit="dB" />
                  <Tooltip contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 12 }} />
                  <Line type="monotone" dataKey="level" stroke="var(--primary)" strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className={breach ? "border-destructive/50 bg-destructive/5" : "border-border/70"}>
            <CardContent className="space-y-3 p-6">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Activity className="size-4" />
                {current === null ? "No readings" : breach ? "Threshold breached" : "Network nominal"}
              </div>
              <p className="font-display text-4xl font-semibold">
                {current === null ? "—" : `${current} dB`}
              </p>
              <p className="text-xs text-muted-foreground">
                {current === null
                  ? "Connect a sensor node and start recording to see live levels."
                  : breach
                    ? "Latest sample is above the acoustic alert threshold."
                    : "Latest sample is below the acoustic alert threshold."}
              </p>
              <Progress value={current === null ? 0 : Math.min((current / 90) * 100, 100)} className="h-2" />
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="font-display text-base">Latest classified events</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {leaks.length === 0 ? (
                <p className="text-muted-foreground">No leak events recorded yet.</p>
              ) : (
                leaks.slice(0, 3).map((l) => (
                  <div key={l.id} className="flex items-center justify-between gap-2">
                    <span className="truncate text-muted-foreground">
                      {l.devices?.code ?? l.reference} · {Number(l.confidence)}%
                    </span>
                    <SeverityBadge severity={l.severity} />
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">Node telemetry</CardTitle>
          <CardDescription>Last ping, firmware and baseline noise floor</CardDescription>
        </CardHeader>
        <CardContent className={devices.length ? "grid gap-4 md:grid-cols-2 xl:grid-cols-4" : undefined}>
          {devices.length === 0 ? (
            <EmptyState
              icon={Radio}
              title="No sensor nodes yet"
              description="Register your acoustic devices to monitor their telemetry."
              action={
                <Button size="sm" asChild>
                  <Link to="/admin">Register a device</Link>
                </Button>
              }
            />
          ) : (
            devices.map((d) => (
              <div key={d.id} className="card-hover rounded-xl border border-border/70 p-4">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-2 text-sm font-medium">
                    <Radio className="size-4 text-primary" /> {d.code}
                  </span>
                  <DeviceStatusBadge status={d.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{d.name}</p>
                <dl className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <div className="flex justify-between"><dt>Baseline</dt><dd>{Number(d.baseline_db)} dB</dd></div>
                  <div className="flex justify-between"><dt>Firmware</dt><dd>{d.firmware || "—"}</dd></div>
                  <div className="flex justify-between">
                    <dt>Last ping</dt>
                    <dd>{d.last_ping ? new Date(d.last_ping).toLocaleTimeString() : "never"}</dd>
                  </div>
                </dl>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
