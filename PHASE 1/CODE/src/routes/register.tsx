import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { redirect } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/routes/login";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";

export const Route = createFileRoute("/register")({
  beforeLoad: () => { throw redirect({ to: "/dashboard" }); },
  head: () => ({
    meta: [
      { title: "Create account — AquaSense Leak Monitoring" },
      { name: "description", content: "Register a monitoring account for the AquaSense acoustic leak detection platform." },
      { property: "og:title", content: "Create account — AquaSense Leak Monitoring" },
      { property: "og:description", content: "Register to monitor pipeline leaks with AI acoustic detection." },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const { signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [zone, setZone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error("Please fill in all fields");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    if (password !== confirm) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    const { error, needsConfirmation } = await signUp(name, email, password, zone || "All zones");
    setLoading(false);
    if (error) {
      toast.error(error);
      return;
    }
    if (needsConfirmation) {
      toast.success("Check your inbox to confirm your email, then sign in");
      navigate({ to: "/login" });
      return;
    }
    toast.success("Account created — welcome to AquaSense");
    navigate({ to: "/dashboard" });
  };

  const google = async () => {
    const { error } = await signInWithGoogle();
    if (error) toast.error(error);
  };

  return (
    <AuthShell title="Create your account" subtitle="Register to access the leak monitoring console.">
      <form onSubmit={submit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="name">Full name</Label>
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="zone">Assigned zone (optional)</Label>
          <Input
            id="zone"
            value={zone}
            onChange={(e) => setZone(e.target.value)}
            placeholder="e.g. North district"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm">Confirm</Label>
            <Input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading && <Loader2 className="mr-2 size-4 animate-spin" />}
          Create account
        </Button>
        <Button type="button" variant="outline" className="w-full" onClick={google}>
          Continue with Google
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already registered?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
