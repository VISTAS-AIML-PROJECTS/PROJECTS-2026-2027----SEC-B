import type { Enums, Tables } from "@/integrations/supabase/types";

export type Severity = Enums<"leak_severity">;
export type DeviceStatus = Enums<"device_status">;
export type LeakStatus = Enums<"leak_status">;
export type UserRole = Enums<"app_role">;
export type NotificationSeverity = Enums<"notification_severity">;

export type Device = Tables<"devices">;
export type Profile = Tables<"profiles">;
export type SensorReading = Tables<"sensor_readings">;
export type AppNotification = Tables<"notifications">;

export type LeakEvent = Tables<"leak_events"> & {
  devices: { code: string; name: string; zone: string } | null;
};
