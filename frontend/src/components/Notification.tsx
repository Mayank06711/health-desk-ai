import { useState, useEffect } from "react";
import { AlertCircle, X } from "lucide-react";

export type NotificationType = "error" | "warning" | "info";

interface NotificationProps {
  type: NotificationType;
  message: string;
  onDismiss?: () => void;
  autoDismiss?: number;
}

export function Notification({
  type,
  message,
  onDismiss,
  autoDismiss = 5000,
}: NotificationProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (autoDismiss > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        onDismiss?.();
      }, autoDismiss);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss, onDismiss]);

  if (!visible) return null;

  const colors = {
    error: "bg-[#FFEBEE] border-[#E53935] text-[#C62828]",
    warning: "bg-[#FFF3E0] border-[#FFA726] text-[#E65100]",
    info: "bg-[#E3F2FD] border-[#2CA3FA] text-[#034C81]",
  };

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${colors[type]} shadow-sm`}
      role="alert"
    >
      <AlertCircle size={18} />
      <span className="text-sm flex-1">{message}</span>
      {onDismiss && (
        <button
          onClick={() => {
            setVisible(false);
            onDismiss();
          }}
          className="opacity-60 hover:opacity-100"
          aria-label="Dismiss"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
