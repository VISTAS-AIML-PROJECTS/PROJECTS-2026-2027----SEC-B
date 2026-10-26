import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Plus, ShieldCheck, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { DeviceStatusBadge, SeverityBadge, StatusBadge } from "@/components/severity-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/use-auth";
import {
  useCreateDevice,
  useDeleteDevice,
  useDevices,
  useLeaks,
  useProfiles,
  useResolveLeak,
} from "@/lib/queries";

export const Route = createFileRoute("/_console/admin")({
  head: () => ({
    meta: [
      { title: "Admin Panel — AquaSense" },
      { name: "description", content: "Manage operators, acoustic sensor devices and leak events across the water network." },
      { property: "og:title", content: "Admin Panel — AquaSense" },
      { property: "og:description", content: "User, device and leak event administration." },
    ],
  }),
  component: AdminPage,
});

function AdminPage() {
  const { role } = useAuth();
  const { data: profiles = [] } = useProfiles();
  const { data: devices = [] } = useDevices();
  const { data: leaks = [] } = useLeaks();
  const createDevice = useCreateDevice();
  const deleteDevice = useDeleteDevice();
  const resolveLeak = useResolveLeak();

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ code: "", name: "", zone: "", pipeline: "" });

  const submit = async () => {
    if (!form.code || !form.name) {
      toast.error("Device code and name are required");
      return;
    }
    try {
      await createDevice.mutateAsync(form);
      toast.success(`${form.code} registered`);
      setForm({ code: "", name: "", zone: "", pipeline: "" });
      setOpen(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not register the device");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin panel"
        description="Manage operators, devices and leak records."
        actions={
          <Badge variant="secondary" className="gap-1 capitalize">
            <ShieldCheck className="size-3" /> {role ?? "no"} access
          </Badge>
        }
      />

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="leaks">Leak events</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-4">
          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="font-display text-lg">Operators</CardTitle>
              <CardDescription>
                {profiles.length} account{profiles.length === 1 ? "" : "s"} with console access
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Zone</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Joined</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {profiles.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.full_name || "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{u.email}</TableCell>
                        <TableCell className="whitespace-nowrap text-muted-foreground">{u.zone}</TableCell>
                        <TableCell>
                          <Badge variant={u.active ? "secondary" : "outline"}>
                            {u.active ? "Active" : "Disabled"}
                          </Badge>
                        </TableCell>
                        <TableCell className="whitespace-nowrap text-muted-foreground">
                          {new Date(u.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                    {profiles.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                          Only administrators can list every operator. Invite teammates by sharing the sign-up page.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="devices" className="mt-4">
          <Card className="border-border/70">
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle className="font-display text-lg">Acoustic devices</CardTitle>
                <CardDescription>
                  {devices.length} registered sensor node{devices.length === 1 ? "" : "s"}
                </CardDescription>
              </div>
              <Dialog open={open} onOpenChange={setOpen}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 size-4" /> Register device
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Register acoustic device</DialogTitle>
                    <DialogDescription>Add a sensor node to your monitoring network.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="code">Device code</Label>
                      <Input
                        id="code"
                        value={form.code}
                        onChange={(e) => setForm({ ...form, code: e.target.value })}
                        placeholder="ACD-01"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="dname">Device name</Label>
                      <Input
                        id="dname"
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="North junction sensor"
                      />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="dzone">Zone</Label>
                        <Input
                          id="dzone"
                          value={form.zone}
                          onChange={(e) => setForm({ ...form, zone: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="dpipe">Pipeline</Label>
                        <Input
                          id="dpipe"
                          value={form.pipeline}
                          onChange={(e) => setForm({ ...form, pipeline: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={submit} disabled={createDevice.isPending}>
                      {createDevice.isPending ? "Saving…" : "Register device"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Zone</TableHead>
                      <TableHead>Pipeline</TableHead>
                      <TableHead>Firmware</TableHead>
                      <TableHead className="text-right">Battery</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {devices.map((d) => (
                      <TableRow key={d.id}>
                        <TableCell className="font-medium">{d.code}</TableCell>
                        <TableCell className="whitespace-nowrap text-muted-foreground">{d.name}</TableCell>
                        <TableCell className="whitespace-nowrap text-muted-foreground">{d.zone || "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{d.pipeline || "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{d.firmware || "—"}</TableCell>
                        <TableCell className="text-right">{d.battery}%</TableCell>
                        <TableCell><DeviceStatusBadge status={d.status} /></TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={async () => {
                              try {
                                await deleteDevice.mutateAsync(d.id);
                                toast.success(`${d.code} removed`);
                              } catch (e) {
                                toast.error(e instanceof Error ? e.message : "Could not remove the device");
                              }
                            }}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {devices.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={8} className="py-10 text-center text-muted-foreground">
                          No devices registered yet — add your first sensor node above.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leaks" className="mt-4">
          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="font-display text-lg">Leak records</CardTitle>
              <CardDescription>
                {leaks.length} event{leaks.length === 1 ? "" : "s"} stored in the archive
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Leak ID</TableHead>
                      <TableHead>Device</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Confidence</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leaks.map((l) => (
                      <TableRow key={l.id}>
                        <TableCell className="font-medium">{l.reference}</TableCell>
                        <TableCell className="whitespace-nowrap text-muted-foreground">
                          {l.devices?.code ?? "—"}
                        </TableCell>
                        <TableCell><SeverityBadge severity={l.severity} /></TableCell>
                        <TableCell><StatusBadge status={l.status} /></TableCell>
                        <TableCell className="text-right">{Number(l.confidence)}%</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={l.status === "resolved"}
                            onClick={async () => {
                              try {
                                await resolveLeak.mutateAsync(l.id);
                                toast.success(`${l.reference} marked resolved`);
                              } catch (e) {
                                toast.error(e instanceof Error ? e.message : "Could not update the leak");
                              }
                            }}
                          >
                            Resolve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {leaks.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                          No leak events recorded yet.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
