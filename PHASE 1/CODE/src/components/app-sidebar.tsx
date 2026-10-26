import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  BarChart3,
  Bell,
  Droplets,
  FileText,
  HelpCircle,
  History,
  LayoutDashboard,
  Settings,
  Shield,
  User,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const monitoring = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "Real-Time Monitoring", url: "/monitoring", icon: Activity },
  { title: "Audio Leak Detection", url: "/detect", icon: FileText },
  { title: "Leak History", url: "/history", icon: History },
  { title: "Notifications", url: "/notifications", icon: Bell },
] as const;

const insights = [
  { title: "Analytics", url: "/analytics", icon: BarChart3 },
  { title: "Reports", url: "/reports", icon: FileText },
] as const;

const account = [
  { title: "Profile", url: "/profile", icon: User },
  { title: "Settings", url: "/settings", icon: Settings },
  { title: "Help & Support", url: "/help", icon: HelpCircle },
  { title: "Admin Panel", url: "/admin", icon: Shield },
] as const;

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  const renderGroup = (label: string, items: readonly { title: string; url: string; icon: typeof Activity }[]) => (
    <SidebarGroup>
      <SidebarGroupLabel>{label}</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.url}>
              <SidebarMenuButton asChild isActive={pathname === item.url} tooltip={item.title}>
                <Link to={item.url} className="flex items-center gap-2">
                  <item.icon className="size-4 shrink-0" />
                  {!collapsed && <span>{item.title}</span>}
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <Link to="/" className="flex items-center gap-2 px-1 py-2">
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary-gradient text-primary-foreground shadow-glow">
            <Droplets className="size-5" />
          </span>
          {!collapsed && (
            <span className="leading-tight">
              <span className="block font-display text-sm font-semibold">AquaSense</span>
              <span className="block text-[11px] text-sidebar-foreground/60">Leak Monitoring</span>
            </span>
          )}
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {renderGroup("Monitoring", monitoring)}
        {renderGroup("Insights", insights)}
        {renderGroup("Account", account)}
      </SidebarContent>
      <SidebarFooter>
        {!collapsed && (
          <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/60 p-3 text-[11px] text-sidebar-foreground/80">
            <p className="font-semibold text-sidebar-foreground">System healthy</p>
            <p className="mt-1">7 of 8 acoustic nodes streaming</p>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
