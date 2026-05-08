import { useState, useCallback } from "react";
import { useDataChannel } from "@livekit/components-react";
import type { ToolCallLog, ToolStatusEvent } from "../types";

export function useToolStatus(): ToolCallLog[] {
  const [logs, setLogs] = useState<ToolCallLog[]>([]);

  const onMessage = useCallback((msg: unknown) => {
    try {
      const raw = msg as { payload: Uint8Array };
      const text = new TextDecoder().decode(raw.payload);
      const event: ToolStatusEvent = JSON.parse(text);
      setLogs((prev) => [
        ...prev,
        {
          tool: event.tool,
          status: event.status,
          timestamp: new Date(),
          data: event.data,
        },
      ]);
    } catch {
      // ignore malformed messages
    }
  }, []);

  useDataChannel("tool-status", onMessage);

  return logs;
}
