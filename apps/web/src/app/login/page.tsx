"use client";

/**
 * Login / register page (Phase 7). Talks to the FastAPI /auth endpoints and
 * stores the JWT token pair in the auth store.
 */
import { useState } from "react";
import { API_URL } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const setSession = useAuthStore((s) => s.setSession);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "register") {
        const r = await fetch(`${API_URL}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, name, password }),
        });
        if (!r.ok) throw new Error((await r.json()).detail ?? "Register failed");
      }
      const r = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) throw new Error((await r.json()).detail ?? "Login failed");
      const tokens = await r.json();
      setSession(tokens.access_token, tokens.refresh_token);
      window.location.href = "/projects";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form onSubmit={submit} className="glass rise w-full max-w-sm space-y-5 p-8">
        <div className="text-center">
          <h1 className="gradient-text text-3xl font-bold tracking-tight">ForgeAI</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </p>
        </div>

        <div className="space-y-3">
          {mode === "register" && (
            <Input label="Name" value={name} onChange={setName} type="text" />
          )}
          <Input label="Email" value={email} onChange={setEmail} type="email" />
          <Input label="Password" value={password} onChange={setPassword} type="password" />
        </div>

        {error && (
          <p className="rounded-lg border border-[var(--red)]/30 bg-[var(--red)]/10 px-3 py-2 text-xs text-[var(--red)]">
            {error}
          </p>
        )}

        <button type="submit" className="btn-primary w-full py-2.5 text-sm">
          {mode === "login" ? "Sign in" : "Create account"}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="w-full text-xs text-[var(--muted)] transition hover:text-[var(--foreground)]"
        >
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </main>
  );
}

function Input({
  label,
  value,
  onChange,
  type,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs text-[var(--muted)]">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full rounded-xl border border-[var(--panel-border)] bg-black/30 px-3 py-2.5 text-sm transition focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/20"
      />
    </label>
  );
}
