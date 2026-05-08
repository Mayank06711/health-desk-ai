import { Loader2, CheckCircle2 } from "lucide-react";
import { useToolStatus } from "../hooks/useToolStatus";

const TOOL_LABELS: Record<string, string> = {
  identify_user: "Identifying patient",
  fetch_slots: "Fetching available slots",
  book_appointment: "Booking appointment",
  retrieve_appointments: "Loading appointments",
  cancel_appointment: "Cancelling appointment",
  modify_appointment: "Modifying appointment",
  end_conversation: "Generating summary",
};

export function ToolStatusPanel() {
  const logs = useToolStatus();

  if (logs.length === 0) return null;

  return (
    <div className="bg-white rounded-xl border border-[#EEF2F7] p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-[#263238] mb-3">Actions</h3>
      <div className="space-y-2">
        {logs.map((log, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            {log.status === "in_progress" ? (
              <Loader2 size={16} className="text-[#2CA3FA] animate-spin" />
            ) : (
              <CheckCircle2 size={16} className="text-[#4CAF50]" />
            )}
            <span
              className={
                log.status === "in_progress"
                  ? "text-[#034C81]"
                  : "text-[#455A64]"
              }
            >
              {TOOL_LABELS[log.tool] || log.tool}
              {log.status === "in_progress" ? "..." : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
