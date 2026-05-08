import { PhoneOff } from "lucide-react";

interface ControlsProps {
  isConnected: boolean;
  onStartCall: () => void;
  onEndCall: () => void;
}

export function Controls({
  isConnected,
  onStartCall,
  onEndCall,
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
    <div className="flex justify-center">
      <button
        onClick={onEndCall}
        className="bg-[#E53935] hover:bg-[#C62828] text-white px-4 py-3 rounded-full transition-colors shadow-sm flex items-center gap-2"
        aria-label="End call"
      >
        <PhoneOff size={20} />
        <span className="text-sm font-medium">End Call</span>
      </button>
    </div>
  );
}
