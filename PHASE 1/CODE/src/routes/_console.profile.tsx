import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { supabase } from "@/integrations/supabase/client";
import { useLeaks } from "@/lib/queries";

export const Route = createFileRoute("/_console/profile")({
  head: () => ({
    meta: [
      { title: "Profile — AquaSense" },
      { name: "description", content: "Manage your AquaSense operator profile, assigned zone and leak assignments." },
      { property: "og:title", content: "Profile — AquaSense" },
      { property: "og:description", content: "Operator profile and assignment history." },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, profile, role, refreshProfile } = useAuth();
  const { data: leaks = [] } = useLeaks();
  const [name, setName] = useState("");
  const [zone, setZone] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(profile?.full_name ?? "");
    setZone(profile?.zone ?? "");
  }, [profile]);

  const initials = (name || user?.email || "O")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const assigned = leaks.filter((l) => l.assigned_to === user?.id);

  const save = async () => {
    if (!user) return;
    setSaving(true);
    const { error } = await supabase
      .from("profiles")
      .update({ full_name: name, zone: zone || "All zones" })
      .eq("id", user.id);
    setSaving(false);
    if (error) {
      toast.error(error.message);
      return;
    }
    await refreshProfile();
    toast.success("Profile updated");
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your operator identity across the monitoring console." />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/70">
          <CardContent className="flex flex-col items-center gap-3 p-6 text-center">
            <Avatar className="size-20">
              <AvatarFallback className="bg-primary/12 font-display text-xl font-semibold text-primary">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-display text-lg font-semibold">{name || "Unnamed operator"}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {role && <Badge variant="secondary" className="capitalize">{role}</Badge>}
              <Badge variant="outline">{profile?.zone || "All zones"}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/70 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-display text-lg">Account details</CardTitle>
            <CardDescription>Displayed on reports and leak assignments</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="pname">Full name</Label>
                <Input id="pname" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pzone">Assigned zone</Label>
                <Input id="pzone" value={zone} onChange={(e) => setZone(e.target.value)} placeholder="All zones" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="pemail">Email</Label>
              <Input id="pemail" value={user?.email ?? ""} readOnly disabled />
            </div>
            <Button onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border/70">
        <CardHeader>
          <CardTitle className="font-display text-lg">My assignments</CardTitle>
          <CardDescription>Leak events assigned to you</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {assigned.length === 0 ? (
            <EmptyState
              title="No assignments yet"
              description="Leak events assigned to you will be listed here."
            />
          ) : (
            assigned.map((l) => (
              <div key={l.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border/70 p-4">
                <div>
                  <p className="font-medium">{l.reference} · {l.zone || l.devices?.zone || "No zone"}</p>
                  <p className="text-xs text-muted-foreground">{l.devices?.name ?? "Unassigned device"}</p>
                </div>
                <Badge variant="outline" className="capitalize">{l.status}</Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
