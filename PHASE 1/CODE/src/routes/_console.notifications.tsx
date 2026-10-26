import { createFileRoute } from "@tanstack/react-router";
import { BellRing, CheckCheck } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMarkNotificationRead, useNotifications } from "@/lib/queries";
import type { AppNotification } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_console/notifications")({
  head: () => ({
    meta: [
      { title: "Notification Center — AquaSense" },
      { name: "description", content: "Severity-graded leak alerts, device warnings and system notices in one inbox." },
      { property: "og:title", content: "Notification Center — AquaSense" },
      { property: "og:description", content: "All leak alerts and device notices for the monitoring network." },
    ],
  }),
  component: NotificationsPage,
});

const tone: Record<string, string> = {
  critical: "bg-destructive/12 text-destructive",
  high: "bg-warning/15 text-warning",
  medium: "bg-primary/12 text-primary",
  low: "bg-success/12 text-success",
  info: "bg-muted text-muted-foreground",
};

function NotificationsPage() {
  const { data: items = [] } = useNotifications();
  const markRead = useMarkNotificationRead();
  const unread = items.filter((n) => !n.read);

  const list = (data: AppNotification[]) => (
    <div className="space-y-3">
      {data.map((n) => (
        <Card key={n.id} className={cn("card-hover border-border/70", !n.read && "border-primary/40 bg-primary/[0.04]")}>
          <CardContent className="flex items-start gap-4 p-4">
            <span className={cn("grid size-10 shrink-0 place-items-center rounded-xl", tone[n.severity])}>
              <BellRing className="size-4" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{n.title}</p>
                <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize", tone[n.severity])}>
                  {n.severity}
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{n.message}</p>
              <p className="mt-2 text-xs text-muted-foreground">{new Date(n.created_at).toLocaleString()}</p>
            </div>
            {!n.read && (
              <Button variant="ghost" size="sm" onClick={() => markRead.mutate([n.id])}>
                Mark read
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
      {data.length === 0 && (
        <EmptyState
          icon={BellRing}
          title="No notifications yet"
          description="Leak alerts and device notices will land here as your network reports them."
        />
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notification center"
        description={`${unread.length} unread alert${unread.length === 1 ? "" : "s"} across the network.`}
        actions={
          <Button
            variant="outline"
            disabled={unread.length === 0}
            onClick={() => {
              markRead.mutate(unread.map((n) => n.id));
              toast.success("All notifications marked as read");
            }}
          >
            <CheckCheck className="mr-2 size-4" /> Mark all read
          </Button>
        }
      />
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All ({items.length})</TabsTrigger>
          <TabsTrigger value="unread">Unread ({unread.length})</TabsTrigger>
          <TabsTrigger value="critical">Critical</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="mt-4">{list(items)}</TabsContent>
        <TabsContent value="unread" className="mt-4">{list(unread)}</TabsContent>
        <TabsContent value="critical" className="mt-4">
          {list(items.filter((n) => n.severity === "critical" || n.severity === "high"))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
