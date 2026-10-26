import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import type { AppNotification, Device, LeakEvent, Profile, SensorReading } from "@/lib/types";

/** All records come from the live database — the app ships with no sample rows. */

export function useDevices() {
  return useQuery({
    queryKey: ["devices"],
    queryFn: async (): Promise<Device[]> => {
      const { data, error } = await supabase.from("devices").select("*").order("code");
      if (error) throw error;
      return data ?? [];
    },
  });
}

export function useLeaks() {
  return useQuery({
    queryKey: ["leak_events"],
    queryFn: async (): Promise<LeakEvent[]> => {
      const { data, error } = await supabase
        .from("leak_events")
        .select("*, devices(code, name, zone)")
        .order("detected_at", { ascending: false });
      if (error) throw error;
      return (data ?? []) as LeakEvent[];
    },
  });
}

export function useReadings(limit = 40) {
  return useQuery({
    queryKey: ["sensor_readings", limit],
    queryFn: async (): Promise<SensorReading[]> => {
      const { data, error } = await supabase
        .from("sensor_readings")
        .select("*")
        .order("recorded_at", { ascending: false })
        .limit(limit);
      if (error) throw error;
      return (data ?? []).slice().reverse();
    },
    refetchInterval: 15_000,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: async (): Promise<AppNotification[]> => {
      const { data, error } = await supabase
        .from("notifications")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data ?? [];
    },
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: ["profiles"],
    queryFn: async (): Promise<Profile[]> => {
      const { data, error } = await supabase.from("profiles").select("*").order("created_at");
      if (error) throw error;
      return data ?? [];
    },
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (ids: string[]) => {
      if (ids.length === 0) return;
      const { error } = await supabase.from("notifications").update({ read: true }).in("id", ids);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useResolveLeak() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("leak_events").update({ status: "resolved" }).eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leak_events"] }),
  });
}

export function useCreateDevice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { code: string; name: string; zone: string; pipeline: string }) => {
      const { error } = await supabase.from("devices").insert(input);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["devices"] }),
  });
}

export function useDeleteDevice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { error } = await supabase.from("devices").delete().eq("id", id);
      if (error) throw error;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["devices"] }),
  });
}

/** Derived analytics — computed from stored leak events, never invented. */
export function zoneCounts(leaks: LeakEvent[]) {
  const map = new Map<string, number>();
  for (const l of leaks) {
    const zone = l.zone || l.devices?.zone || "Unassigned";
    map.set(zone, (map.get(zone) ?? 0) + 1);
  }
  return [...map.entries()].map(([zone, leaks]) => ({ zone, leaks }));
}

export function severityCounts(leaks: LeakEvent[]) {
  const order = ["critical", "high", "medium", "low"] as const;
  return order
    .map((name) => ({ name, value: leaks.filter((l) => l.severity === name).length }))
    .filter((s) => s.value > 0);
}

export function weeklyCounts(leaks: LeakEvent[]) {
  const map = new Map<string, { week: string; leaks: number; resolved: number; loss: number }>();
  for (const l of leaks) {
    const d = new Date(l.detected_at);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
      Math.ceil(d.getDate() / 7),
    )}`;
    const label = `${d.toLocaleString(undefined, { month: "short" })} W${Math.ceil(d.getDate() / 7)}`;
    const row = map.get(key) ?? { week: label, leaks: 0, resolved: 0, loss: 0 };
    row.leaks += 1;
    if (l.status === "resolved") row.resolved += 1;
    row.loss += Number(l.estimated_loss_lpm);
    map.set(key, row);
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([, v]) => v);
}
