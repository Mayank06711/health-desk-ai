import { Mic, MicOff, PhoneOff } from "lucide-react";

interface ControlsProps {
  isConnected: boolean;
  isMuted: boolean;
  onStartCall: () => void;
  onEndCall: () => void;
  onToggleMic: () => void;
}

export function Controls({
  isConnected,
  isMuted,
  onStartCall,
  onEndCall,
  onToggleMic,
}: ControlsProps) {
  if (!isConnected) {
    return (
      <div className="flex justify-center">
        <button
          onClick={onStartCall}
          className="bg-[#034C81] hover:bg-[#023a63] text-white px-8 py-3 rounded-full text-lg font-medium transition-colors shadow-md"
        >
          Start Call
        </button>
      </div>
    );
  }

  return (
    <div className="flex justify-center gap-4">
      <button
        onClick={onToggleMic}
        className={`p-3 rounded-full transition-colors shadow-sm ${
          isMuted
            ? "bg-[#FFEBEE] text-[#E53935] hover:bg-[#FFCDD2]"
            : "bg-[#EEF2F7] text-[#455A64] hover:bg-[#E0E5EB]"
        }`}
        aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}
      >
        {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
      </button>
      <button
        onClick={onEndCall}
        className="bg-[#E53935] hover:bg-[#C62828] text-white p-3 rounded-full transition-colors shadow-sm"
        aria-label="End call"
      >
        <PhoneOff size={24} />
      </button>
    </div>
  );
}
