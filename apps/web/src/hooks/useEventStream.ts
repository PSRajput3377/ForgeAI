"use client";

import { useEffect, useRef, useState } from "react";
import { WS_URL, type ForgeEvent } from "@/lib/api";

/**
 * Subscribe to the backend's live event WebSocket. Returns the rolling list of
 * events and the connection status — no polling.
 */
export function useEventStream(max = 200) {
  const [events, setEvents] = useState<ForgeEvent[]>([]);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting",
  );
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/observability/live`);
    wsRef.current = ws;
    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("closed");
    ws.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data) as ForgeEvent;
        setEvents((prev) => [...prev.slice(-(max - 1)), event]);
      } catch {
        // ignore malformed frames
      }
    };
    return () => ws.close();
  }, [max]);

  return { events, status };
}
