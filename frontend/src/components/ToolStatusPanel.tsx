import { Loader2, CheckCircle2 } from "lucide-react";
import { useToolStatus } from "../hooks/useToolStatus";
import type { ToolCallLog } from "../types";

const TOOL_LABELS: Record<string, string> = {
  identify_user: "Identifying patient",
  fetch_slots: "Fetching available slots",
  book_appointment: "Booking appointment",
  retrieve_appointments: "Loading appointments",
  cancel_appointment: "Cancelling appointment",
  modify_appointment: "Modifying appointment",
  end_conversation: "Generating summary",
};

function mergeToolLogs(logs: ToolCallLog[]): ToolCallLog[] {
  const merged: ToolCallLog[] = [];
  const seen = new Map<string, number>();

  for (const log of logs) {
    if (log.status === "in_progress") {
      seen.set(log.tool, (seen.get(log.tool) ?? 0) + 1);
      merged.push({ ...log });
    } else if (log.status === "completed") {
      const idx = merged.findLastIndex(
        (m) => m.tool === log.tool && m.status === "in_progress"
      );
      if (idx >= 0) {
        merged[idx] = { ...merged[idx], status: "completed", data: log.data };
      } else {
        merged.push({ ...log });
      }
    }
  }
  return merged;
}

export function ToolStatusPanel() {
  const logs = useToolStatus();
  const merged = mergeToolLogs(logs);

  if (merged.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-[#EEF2F7] p-4 shadow-sm max-h-48 overflow-y-auto">
      <h3 className="text-sm font-semibold text-[#263238] mb-3 sticky top-0 bg-white">
        Actions
      </h3>
      <div className="space-y-2">
        {merged.map((log, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            {log.status === "in_progress" ? (
              <Loader2
                size={16}
                className="text-[#2CA3FA] animate-spin shrink-0"
              />
            ) : (
              <CheckCircle2 size={16} className="text-[#4CAF50] shrink-0" />
            )}
            <span
              className={
                log.status === "in_progress"
                  ? "text-[#034C81]"
                  : "text-[#455A64]"
              }
            >
              {TOOL_LABELS[log.tool] || log.tool}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
