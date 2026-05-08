import { FileText, Calendar, Clock, Download, ChevronUp, ChevronDown } from "lucide-react";
import { useState } from "react";
import { useCallSummary } from "../hooks/useCallSummary";

function downloadSummary(
  summary: NonNullable<ReturnType<typeof useCallSummary>>
) {
  const lines = [
    "HEALTH DESK AI — APPOINTMENT SUMMARY",
    "=".repeat(40),
    "",
    `Date: ${new Date(summary.timestamp).toLocaleString()}`,
    "",
    "SUMMARY",
    summary.summary,
    "",
  ];

  if (summary.appointments.length > 0) {
    lines.push("APPOINTMENTS");
    summary.appointments.forEach((a, i) => {
      lines.push(`  ${i + 1}. ${a.date} at ${a.time} — ${a.status}`);
    });
    lines.push("");
  }

  if (summary.preferences.length > 0) {
    lines.push("PREFERENCES");
    summary.preferences.forEach((p) => lines.push(`  - ${p}`));
    lines.push("");
  }

  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `appointment-summary-${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

export function CallSummary() {
  const summary = useCallSummary();
  const [minimized, setMinimized] = useState(false);

  if (!summary) return null;

  // Minimized widget — small bar on bottom-right
  if (minimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <div className="bg-white rounded-xl shadow-lg border border-[#EEF2F7] p-3 flex items-center gap-3">
          <FileText size={16} className="text-[#034C81]" />
          <span className="text-sm font-medium text-[#263238]">
            Call Summary
          </span>
          <button
            onClick={() => downloadSummary(summary)}
            className="text-[#034C81] hover:text-[#023a63]"
            aria-label="Download summary"
          >
            <Download size={16} />
          </button>
          <button
            onClick={() => setMinimized(false)}
            className="text-[#455A64] hover:text-[#263238]"
            aria-label="Expand summary"
          >
            <ChevronUp size={16} />
          </button>
        </div>
      </div>
    );
  }

  // Full summary panel — overlay
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#EEF2F7] max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText size={20} className="text-[#034C81]" />
            <h2 className="text-lg font-semibold text-[#263238]">
              Call Summary
            </h2>
          </div>
          <button
            onClick={() => setMinimized(true)}
            className="text-[#B0BEC5] hover:text-[#455A64] flex items-center gap-1 text-sm"
            aria-label="Minimize summary"
          >
            Minimize <ChevronDown size={16} />
          </button>
        </div>

        <div className="space-y-4">
          {summary.summary && (
            <div>
              <h3 className="text-sm font-medium text-[#455A64] mb-1">
                Summary
              </h3>
              <p className="text-[#263238]">{summary.summary}</p>
            </div>
          )}

          {summary.appointments && summary.appointments.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-[#455A64] mb-2">
                Appointments
              </h3>
              <div className="space-y-2">
                {summary.appointments.map((appt, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 bg-[#F5F7FA] rounded-lg p-3"
                  >
                    <Calendar size={16} className="text-[#034C81]" />
                    <span className="text-sm text-[#263238]">
                      {appt.date || "N/A"}
                    </span>
                    <Clock size={16} className="text-[#034C81]" />
                    <span className="text-sm text-[#263238]">
                      {appt.time || "N/A"}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        appt.status === "booked"
                          ? "bg-[#E8F5E9] text-[#2E7D32]"
                          : "bg-[#FFEBEE] text-[#C62828]"
                      }`}
                    >
                      {appt.status || "unknown"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {summary.preferences && summary.preferences.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-[#455A64] mb-1">
                Preferences
              </h3>
              <ul className="text-sm text-[#455A64] list-disc list-inside">
                {summary.preferences.map((pref, i) => (
                  <li key={i}>{pref}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center justify-between pt-3 border-t border-[#EEF2F7]">
            <span className="text-xs text-[#B0BEC5]">
              {summary.timestamp
                ? new Date(summary.timestamp).toLocaleString()
                : "Just now"}
            </span>
            <button
              onClick={() => downloadSummary(summary)}
              className="flex items-center gap-1 text-sm text-[#034C81] hover:text-[#023a63] font-medium"
            >
              <Download size={16} />
              Download
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
