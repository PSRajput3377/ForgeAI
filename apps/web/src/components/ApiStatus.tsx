"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Pings the backend /health endpoint to prove frontend↔backend wiring works. */
export function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "ok" | "down">("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => (r.ok ? setStatus("ok") : setStatus("down")))
      .catch(() => setStatus("down"));
  }, []);

  const label = {
    checking: "Checking API…",
    ok: "API connected",
    down: "API unreachable",
  }[status];

  const color = {
    checking: "bg-yellow-500",
    ok: "bg-green-500",
    down: "bg-red-500",
  }[status];

  return (
    <div className="chip inline-flex items-center gap-2 px-4 py-2">
      <span className={`h-2 w-2 rounded-full ${color} ${status === "ok" ? "pulse-ring" : ""}`} />
      <span className="text-sm text-[var(--muted)]">{label}</span>
    </div>
  );
}
