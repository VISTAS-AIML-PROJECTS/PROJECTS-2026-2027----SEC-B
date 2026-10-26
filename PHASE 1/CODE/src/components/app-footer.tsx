import { Link } from "@tanstack/react-router";
import { Droplets } from "lucide-react";

export function AppFooter() {
  return (
    <footer className="border-t border-border/70 bg-surface-gradient">
      <div className="mx-auto w-full max-w-7xl px-6 py-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-sm">
            <div className="flex items-center gap-2">
              <span className="grid size-8 place-items-center rounded-lg bg-primary-gradient text-primary-foreground">
                <Droplets className="size-4" />
              </span>
              <span className="font-display text-sm font-semibold">AquaSense Monitor</span>
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              AI-based acoustic water leakage detection platform. Final year engineering project —
              edge acoustic sensing, deep-learning classification and real-time municipal alerting.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-8 text-xs sm:grid-cols-3">
            <div className="space-y-2">
              <p className="font-semibold uppercase tracking-wider text-muted-foreground">Platform</p>
              <Link to="/dashboard" className="block text-muted-foreground hover:text-primary">Dashboard</Link>
              <Link to="/monitoring" className="block text-muted-foreground hover:text-primary">Live monitoring</Link>
              <Link to="/analytics" className="block text-muted-foreground hover:text-primary">Analytics</Link>
            </div>
            <div className="space-y-2">
              <p className="font-semibold uppercase tracking-wider text-muted-foreground">Operations</p>
              <Link to="/history" className="block text-muted-foreground hover:text-primary">Leak history</Link>
              <Link to="/reports" className="block text-muted-foreground hover:text-primary">Reports</Link>
              <Link to="/admin" className="block text-muted-foreground hover:text-primary">Admin panel</Link>
            </div>
            <div className="space-y-2">
              <p className="font-semibold uppercase tracking-wider text-muted-foreground">Support</p>
              <Link to="/help" className="block text-muted-foreground hover:text-primary">Help center</Link>
              <Link to="/settings" className="block text-muted-foreground hover:text-primary">Settings</Link>
              <Link to="/profile" className="block text-muted-foreground hover:text-primary">Profile</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 flex flex-col gap-2 border-t border-border/70 pt-4 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 AquaSense Monitor — Department of Engineering. All rights reserved.</p>
          <p>Acoustic model v2.4.1 · 96.4% detection accuracy</p>
        </div>
      </div>
    </footer>
  );
}
