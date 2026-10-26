import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { redirect } from "@tanstack/react-router";
import { useState } from "react";
import { Droplets, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";

export const Route = createFileRoute("/login")({
  beforeLoad: () => { throw redirect({ to: "/dashboard" }); },
  head: () => ({
    meta: [
      { title: "Sign in — AquaSense Leak Monitoring" },
      { name: "description", content: "Sign in to the AquaSense acoustic water leak monitoring console." },
      { property: "og:title", content: "Sign in — AquaSense Leak Monitoring" },
      { property: "og:description", content: "Secure access to live pipeline leak monitoring dashboards." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { signIn, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Enter your email and password");
      return;
    }
    setLoading(true);
    const { error } = await signIn(email, password);
    setLoading(false);
    if (error) {
      toast.error(error);
      return;
    }
    toast.success("Signed in — welcome back");
    navigate({ to: "/dashboard" });
  };

  const google = async () => {
    const { error } = await signInWithGoogle();
    if (error) toast.error(error);
  };

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to monitor your acoustic sensor network.">
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading && <Loader2 className="mr-2 size-4 animate-spin" />}
          Sign in
        </Button>
        <Button type="button" variant="outline" className="w-full" onClick={google}>
          Continue with Google
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          New here?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-hero-gradient p-10 text-primary-foreground lg:flex">
        <Link to="/" className="flex items-center gap-2">
          <span className="grid size-9 place-items-center rounded-xl bg-white/15">
            <Droplets className="size-5" />
          </span>
          <span className="font-display text-base font-semibold">AquaSense</span>
        </Link>
        <div className="space-y-4">
          <h2 className="font-display text-3xl font-bold leading-tight">
            AI-based acoustic water leakage detection
          </h2>
          <p className="max-w-md text-sm text-primary-foreground/80">
            Continuous pipeline listening, deep-learning leak classification and severity-graded
            dispatch for municipal water networks.
          </p>
        </div>
        <p className="text-xs text-primary-foreground/60">
          Final year engineering project · Department of Engineering
        </p>
      </div>
      <div className="flex items-center justify-center p-6">
        <Card className="animate-fade-up w-full max-w-md border-border/70 shadow-elegant">
          <CardHeader>
            <CardTitle className="font-display text-2xl">{title}</CardTitle>
            <CardDescription>{subtitle}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </div>
    </div>
  );
}
