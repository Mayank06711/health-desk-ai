import { useState } from "react";
import { FileText, Calendar, Clock, X } from "lucide-react";
import { useCallSummary } from "../hooks/useCallSummary";

export function CallSummary() {
  const summary = useCallSummary();
  const [dismissed, setDismissed] = useState(false);

  if (!summary || dismissed) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#EEF2F7]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText size={20} className="text-[#034C81]" />
            <h2 className="text-lg font-semibold text-[#263238]">
              Call Summary
            </h2>
          </div>
          <button
            onClick={() => setDismissed(true)}
            className="text-[#B0BEC5] hover:text-[#455A64]"
            aria-label="Close summary"
          >
            <X size={20} />
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

          <div className="text-xs text-[#B0BEC5] pt-2 border-t border-[#EEF2F7]">
            {summary.timestamp
              ? new Date(summary.timestamp).toLocaleString()
              : "Just now"}
          </div>
        </div>
      </div>
    </div>
  );
}
