import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/hooks/use-theme";

export const Route = createFileRoute("/_console/settings")({
  head: () => ({
    meta: [
      { title: "Settings — AquaSense" },
      { name: "description", content: "Configure acoustic alert thresholds, notification channels, appearance and data retention." },
      { property: "og:title", content: "Settings — AquaSense" },
      { property: "og:description", content: "System preferences for the leak monitoring console." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const [threshold, setThreshold] = useState([55]);
  const [confidence, setConfidence] = useState([80]);
  const [email, setEmail] = useState(true);
  const [sms, setSms] = useState(false);
  const [push, setPush] = useState(true);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        description="Tune detection sensitivity and how the system alerts your team."
        actions={<Button onClick={() => toast.success("Settings saved")}>Save settings</Button>}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="font-display text-lg">Detection thresholds</CardTitle>
            <CardDescription>Applied to every acoustic node in the network</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <Label>Acoustic alert threshold</Label>
                <span className="font-medium">{threshold[0]} dB</span>
              </div>
              <Slider value={threshold} onValueChange={setThreshold} min={30} max={90} step={1} />
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <Label>Minimum classifier confidence</Label>
                <span className="font-medium">{confidence[0]}%</span>
              </div>
              <Slider value={confidence} onValueChange={setConfidence} min={50} max={99} step={1} />
            </div>
            <Separator />
            <div className="space-y-2">
              <Label htmlFor="interval">Sampling interval</Label>
              <Select defaultValue="1500">
                <SelectTrigger id="interval"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="500">0.5 seconds</SelectItem>
                  <SelectItem value="1500">1.5 seconds</SelectItem>
                  <SelectItem value="5000">5 seconds</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="font-display text-lg">Notifications</CardTitle>
              <CardDescription>Channels used for leak alerts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { label: "Email alerts", value: email, set: setEmail },
                { label: "SMS alerts", value: sms, set: setSms },
                { label: "Browser push", value: push, set: setPush },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between">
                  <Label className="text-sm font-normal">{row.label}</Label>
                  <Switch checked={row.value} onCheckedChange={row.set} />
                </div>
              ))}
              <Separator />
              <div className="space-y-2">
                <Label htmlFor="recipient">Escalation recipient</Label>
                <Input id="recipient" defaultValue="control-room@aquasense.io" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="font-display text-lg">Appearance & data</CardTitle>
              <CardDescription>Console theme and retention policy</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-normal">Dark mode</Label>
                <Switch checked={theme === "dark"} onCheckedChange={toggleTheme} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="retention">Event retention</Label>
                <Select defaultValue="365">
                  <SelectTrigger id="retention"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="90">90 days</SelectItem>
                    <SelectItem value="365">1 year</SelectItem>
                    <SelectItem value="1825">5 years</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
