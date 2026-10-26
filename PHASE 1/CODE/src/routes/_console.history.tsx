import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { FileSpreadsheet, FileText, Search } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { SeverityBadge, StatusBadge } from "@/components/severity-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useLeaks } from "@/lib/queries";

export const Route = createFileRoute("/_console/history")({
  head: () => ({
    meta: [
      { title: "Leak History — AquaSense" },
      { name: "description", content: "Searchable archive of detected leak events with severity, confidence and export to PDF or Excel." },
      { property: "og:title", content: "Leak History — AquaSense" },
      { property: "og:description", content: "Full leak event archive with filters and export options." },
    ],
  }),
  component: HistoryPage,
});

function HistoryPage() {
  const { data: leaks = [] } = useLeaks();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");

  const rows = useMemo(
    () =>
      leaks.filter(
        (l) =>
          (severity === "all" || l.severity === severity) &&
          (status === "all" || l.status === status) &&
          `${l.reference} ${l.devices?.code ?? ""} ${l.devices?.name ?? ""} ${l.zone}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [leaks, query, severity, status],
  );

  const exportCsv = () => {
    if (rows.length === 0) {
      toast.error("There are no leak records to export yet");
      return;
    }
    const header = ["Reference", "Device", "Zone", "Severity", "Status", "Confidence", "Loss (L/min)", "Detected"];
    const body = rows.map((l) => [
      l.reference,
      l.devices?.code ?? "",
      l.zone || l.devices?.zone || "",
      l.severity,
      l.status,
      String(l.confidence),
      String(l.estimated_loss_lpm),
      new Date(l.detected_at).toISOString(),
    ]);
    const csv = [header, ...body].map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "aquasense-leak-history.csv";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Leak history downloaded");
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leak history"
        description={`${rows.length} of ${leaks.length} recorded acoustic leak events.`}
        actions={
          <>
            <Button variant="outline" onClick={() => window.print()}>
              <FileText className="mr-2 size-4" /> Print / PDF
            </Button>
            <Button onClick={exportCsv}>
              <FileSpreadsheet className="mr-2 size-4" /> Export spreadsheet
            </Button>
          </>
        }
      />

      <Card className="border-border/70">
        <CardContent className="space-y-4 p-4 sm:p-6">
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search leak reference, device or zone"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <Select value={severity} onValueChange={setSeverity}>
              <SelectTrigger className="sm:w-44"><SelectValue placeholder="Severity" /></SelectTrigger>
              <SelectContent>
                {["all", "critical", "high", "medium", "low"].map((s) => (
                  <SelectItem key={s} value={s} className="capitalize">{s === "all" ? "All severities" : s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="sm:w-44"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                {["all", "active", "investigating", "resolved"].map((s) => (
                  <SelectItem key={s} value={s} className="capitalize">{s === "all" ? "All statuses" : s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="overflow-x-auto rounded-xl border border-border/70">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Leak ID</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead>Zone</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Confidence</TableHead>
                  <TableHead className="text-right">Loss (L/min)</TableHead>
                  <TableHead>Detected</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="font-medium">{l.reference}</TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">{l.devices?.code ?? "—"}</TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {l.zone || l.devices?.zone || "—"}
                    </TableCell>
                    <TableCell><SeverityBadge severity={l.severity} /></TableCell>
                    <TableCell><StatusBadge status={l.status} /></TableCell>
                    <TableCell className="text-right">{Number(l.confidence)}%</TableCell>
                    <TableCell className="text-right">{Number(l.estimated_loss_lpm)}</TableCell>
                    <TableCell className="whitespace-nowrap text-muted-foreground">
                      {new Date(l.detected_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
                {rows.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="py-10 text-center text-muted-foreground">
                      {leaks.length === 0
                        ? "No leak events recorded yet."
                        : "No leak events match these filters."}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
