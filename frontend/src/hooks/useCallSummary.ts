import { useState, useCallback } from "react";
import { useDataChannel } from "@livekit/components-react";
import type { CallSummaryData } from "../types";

export function useCallSummary(): CallSummaryData | null {
  const [summary, setSummary] = useState<CallSummaryData | null>(null);

  const onMessage = useCallback((msg: unknown) => {
    try {
      const raw = msg as { payload: Uint8Array };
      const text = new TextDecoder().decode(raw.payload);
      const data: CallSummaryData = JSON.parse(text);
      setSummary(data);
    } catch {
      // ignore malformed messages
    }
  }, []);

  useDataChannel("call-summary", onMessage);

  return summary;
}
