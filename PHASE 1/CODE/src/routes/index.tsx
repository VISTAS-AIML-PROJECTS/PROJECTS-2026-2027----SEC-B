import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  BarChart3,
  Bell,
  BrainCircuit,
  Droplets,
  Gauge,
  ShieldCheck,
  Waves,
} from "lucide-react";
import { AppFooter } from "@/components/app-footer";
import { LiveIndicator } from "@/components/severity-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AquaSense — AI Acoustic Water Leak Detection Platform" },
      {
        name: "description",
        content:
          "Detect water pipeline leaks in seconds with AI acoustic sensing, live dashboards, severity alerts and zone analytics.",
      },
      { property: "og:title", content: "AquaSense — AI Acoustic Water Leak Detection Platform" },
      {
        property: "og:description",
        content:
          "Smart Water Leak Monitoring System: real-time acoustic detection, severity classification and municipal reporting.",
      },
    ],
  }),
  component: Landing,
});

const features = [
  { icon: BrainCircuit, title: "AI acoustic classification", text: "Deep-learning model separates leak signatures from ambient pipeline noise." },
  { icon: Activity, title: "Real-time monitoring", text: "Live dB and frequency streams from every acoustic node with threshold breach alerts." },
  { icon: Bell, title: "Instant notifications", text: "Severity-graded alerts routed to the right field engineer within seconds." },
  { icon: BarChart3, title: "Analytics & reports", text: "Zone-wise trends, water saved and exportable PDF/Excel reports for review boards." },
  { icon: Gauge, title: "Device health", text: "Battery, signal and firmware telemetry for the entire sensor fleet." },
  { icon: ShieldCheck, title: "Role-based access", text: "Admin, engineer and viewer roles backed by secure cloud authentication." },
];

function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center gap-3 px-6">
          <span className="grid size-9 place-items-center rounded-xl bg-primary-gradient text-primary-foreground shadow-glow">
            <Droplets className="size-5" />
          </span>
          <span className="font-display text-base font-semibold">AquaSense</span>
          <div className="ml-auto flex items-center gap-2">
            <Button asChild>
              <Link to="/dashboard">Open dashboard</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="bg-hero-gradient text-primary-foreground">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div className="animate-fade-up space-y-6">
            <LiveIndicator label="Live acoustic monitoring" className="border-white/25 bg-white/10 text-white" />
            <h1 className="font-display text-4xl font-bold leading-tight sm:text-5xl">
              Smart Water Leak Monitoring System
            </h1>
            <p className="max-w-xl text-base text-primary-foreground/85">
              An AI-based acoustic water leakage detection platform that listens to municipal
              pipelines, classifies leak signatures in real time and dispatches severity-graded
              alerts before water loss escalates.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" variant="secondary" asChild>
                <Link to="/dashboard">Launch live demo</Link>
              </Button>
            </div>
            <ul className="grid max-w-md gap-2 pt-2 text-sm text-primary-foreground/80 sm:grid-cols-2">
              <li>Acoustic sensor fleet management</li>
              <li>Severity-graded leak alerts</li>
              <li>Zone-wise water loss analytics</li>
              <li>Board-ready exportable reports</li>
            </ul>
          </div>
          <div className="animate-fade-up rounded-2xl border border-white/20 bg-white/10 p-6 backdrop-blur">
            <div className="flex items-center justify-between text-sm font-medium">
              <span className="inline-flex items-center gap-2">
                <Waves className="size-4" /> Acoustic waveform view
              </span>
            </div>
            <div className="mt-6 flex h-40 items-end gap-1.5">
              {Array.from({ length: 34 }).map((_, i) => {
                const h = Math.round(18 + Math.abs(Math.sin(i / 2.2)) * 55);
                return (
                  <span
                    key={i}
                    className="flex-1 rounded-t bg-white/80"
                    style={{ height: `${Math.min(h, 100)}%`, opacity: "0.65" }}
                  />
                );
              })}
            </div>
            <p className="mt-6 text-xs text-primary-foreground/70">
              Sign in to stream live decibel and frequency readings from your own sensor nodes.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-7xl px-6 py-16">
        <h2 className="font-display text-2xl font-semibold sm:text-3xl">Platform capabilities</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Everything required for an end-to-end leak detection deployment — from edge acoustic
          sensing to board-ready reporting.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title} className="card-hover border-border/70">
              <CardContent className="space-y-3 p-6">
                <span className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
                  <f.icon className="size-5" />
                </span>
                <h3 className="font-display text-base font-semibold">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.text}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <AppFooter />
    </div>
  );
}
