export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.17"
  }
  public: {
    Tables: {
      devices: {
        Row: {
          baseline_db: number
          battery: number
          code: string
          created_at: string
          firmware: string
          id: string
          last_ping: string | null
          name: string
          pipeline: string
          signal: number
          status: Database["public"]["Enums"]["device_status"]
          zone: string
        }
        Insert: {
          baseline_db?: number
          battery?: number
          code: string
          created_at?: string
          firmware?: string
          id?: string
          last_ping?: string | null
          name: string
          pipeline?: string
          signal?: number
          status?: Database["public"]["Enums"]["device_status"]
          zone?: string
        }
        Update: {
          baseline_db?: number
          battery?: number
          code?: string
          created_at?: string
          firmware?: string
          id?: string
          last_ping?: string | null
          name?: string
          pipeline?: string
          signal?: number
          status?: Database["public"]["Enums"]["device_status"]
          zone?: string
        }
        Relationships: []
      }
      leak_events: {
        Row: {
          acoustic_db: number
          assigned_to: string | null
          confidence: number
          created_at: string
          detected_at: string
          device_id: string | null
          estimated_loss_lpm: number
          frequency_hz: number
          id: string
          reference: string
          severity: Database["public"]["Enums"]["leak_severity"]
          status: Database["public"]["Enums"]["leak_status"]
          zone: string
        }
        Insert: {
          acoustic_db?: number
          assigned_to?: string | null
          confidence?: number
          created_at?: string
          detected_at?: string
          device_id?: string | null
          estimated_loss_lpm?: number
          frequency_hz?: number
          id?: string
          reference?: string
          severity?: Database["public"]["Enums"]["leak_severity"]
          status?: Database["public"]["Enums"]["leak_status"]
          zone?: string
        }
        Update: {
          acoustic_db?: number
          assigned_to?: string | null
          confidence?: number
          created_at?: string
          detected_at?: string
          device_id?: string | null
          estimated_loss_lpm?: number
          frequency_hz?: number
          id?: string
          reference?: string
          severity?: Database["public"]["Enums"]["leak_severity"]
          status?: Database["public"]["Enums"]["leak_status"]
          zone?: string
        }
        Relationships: [
          {
            foreignKeyName: "leak_events_device_id_fkey"
            columns: ["device_id"]
            isOneToOne: false
            referencedRelation: "devices"
            referencedColumns: ["id"]
          },
        ]
      }
      notifications: {
        Row: {
          created_at: string
          id: string
          message: string
          read: boolean
          severity: Database["public"]["Enums"]["notification_severity"]
          title: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          message?: string
          read?: boolean
          severity?: Database["public"]["Enums"]["notification_severity"]
          title: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          message?: string
          read?: boolean
          severity?: Database["public"]["Enums"]["notification_severity"]
          title?: string
          user_id?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          active: boolean
          created_at: string
          email: string
          full_name: string
          id: string
          zone: string
        }
        Insert: {
          active?: boolean
          created_at?: string
          email?: string
          full_name?: string
          id: string
          zone?: string
        }
        Update: {
          active?: boolean
          created_at?: string
          email?: string
          full_name?: string
          id?: string
          zone?: string
        }
        Relationships: []
      }
      sensor_readings: {
        Row: {
          acoustic_db: number
          device_id: string
          frequency_hz: number | null
          id: string
          recorded_at: string
        }
        Insert: {
          acoustic_db: number
          device_id: string
          frequency_hz?: number | null
          id?: string
          recorded_at?: string
        }
        Update: {
          acoustic_db?: number
          device_id?: string
          frequency_hz?: number | null
          id?: string
          recorded_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "sensor_readings_device_id_fkey"
            columns: ["device_id"]
            isOneToOne: false
            referencedRelation: "devices"
            referencedColumns: ["id"]
          },
        ]
      }
      user_roles: {
        Row: {
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "admin" | "engineer" | "viewer"
      device_status: "online" | "offline" | "maintenance"
      leak_severity: "critical" | "high" | "medium" | "low"
      leak_status: "active" | "investigating" | "resolved"
      notification_severity: "critical" | "high" | "medium" | "low" | "info"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["admin", "engineer", "viewer"],
      device_status: ["online", "offline", "maintenance"],
      leak_severity: ["critical", "high", "medium", "low"],
      leak_status: ["active", "investigating", "resolved"],
      notification_severity: ["critical", "high", "medium", "low", "info"],
    },
  },
} as const
