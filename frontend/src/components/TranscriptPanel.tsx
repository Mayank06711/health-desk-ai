import { useEffect, useRef, useState, useCallback } from "react";
import { useDataChannel } from "@livekit/components-react";

interface TranscriptEntry {
  role: "user" | "agent";
  text: string;
  timestamp: Date;
}

export function TranscriptPanel() {
  const [entries, setEntries] = useState<TranscriptEntry[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const onMessage = useCallback((msg: unknown) => {
    try {
      const raw = msg as { payload: Uint8Array };
      const text = new TextDecoder().decode(raw.payload);
      const data = JSON.parse(text);
      if (data.role && data.text) {
        setEntries((prev) => [
          ...prev,
          { role: data.role, text: data.text, timestamp: new Date() },
        ]);
      }
    } catch {
      // ignore
    }
  }, []);

  useDataChannel("transcript", onMessage);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-[#EEF2F7] p-4 h-64 flex items-center justify-center shadow-sm">
        <p className="text-[#B0BEC5] text-sm">
          Conversation will appear here...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-[#EEF2F7] p-4 h-64 overflow-y-auto shadow-sm">
      <h3 className="text-sm font-semibold text-[#263238] mb-3">Transcript</h3>
      <div className="space-y-2">
        {entries.map((entry, i) => (
          <div key={i} className="text-sm">
            <span
              className={`font-medium ${
                entry.role === "user" ? "text-[#2CA3FA]" : "text-[#034C81]"
              }`}
            >
              {entry.role === "user" ? "You" : "Assistant"}:
            </span>{" "}
            <span className="text-[#455A64]">{entry.text}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
