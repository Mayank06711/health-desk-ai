import { useState, useCallback } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { fetchToken } from "../services/api";
import { AvatarDisplay } from "./AvatarDisplay";
import { ToolStatusPanel } from "./ToolStatusPanel";
import { TranscriptPanel } from "./TranscriptPanel";
import { CallSummary } from "./CallSummary";
import { Controls } from "./Controls";
import { Notification } from "./Notification";

function RoomContent({ onDisconnect }: { onDisconnect: () => void }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col items-center gap-4">
          <AvatarDisplay />
        </div>
        <div className="flex flex-col gap-4">
          <TranscriptPanel />
          <ToolStatusPanel />
        </div>
      </div>
      <div className="sticky bottom-0 bg-[#F5F7FA] py-3">
        <Controls
          isConnected={true}
          onStartCall={() => {}}
          onEndCall={onDisconnect}
        />
      </div>
      <CallSummary />
      <RoomAudioRenderer />
    </div>
  );
}

export function VoiceAgent() {
  const [connectionState, setConnectionState] = useState<{
    token: string;
    url: string;
  } | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCall = useCallback(async () => {
    setError(null);
    setIsConnecting(true);

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError(
        "Microphone access is required for voice calls. Please allow microphone permission."
      );
      setIsConnecting(false);
      return;
    }

    try {
      const identity = `patient-${Date.now()}`;
      const { token, url } = await fetchToken(identity);

      if (!token || !url) {
        setError("Received invalid connection details. Please try again.");
        setIsConnecting(false);
        return;
      }

      setConnectionState({ token, url });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error occurred";
      if (
        message.includes("Failed to fetch") ||
        message.includes("NetworkError")
      ) {
        setError(
          "Cannot reach the server. Make sure the backend is running on port 8000."
        );
      } else {
        setError(`Connection failed: ${message}`);
      }
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setConnectionState(null);
    setError(null);
  }, []);

  const handleRoomError = useCallback((err: Error) => {
    console.error("Room error:", err);
    setError(`Connection lost: ${err.message}`);
    setConnectionState(null);
  }, []);

  if (!connectionState) {
    return (
      <div className="flex flex-col items-center gap-8 py-16">
        <div className="w-24 h-24 rounded-full bg-[#034C81] flex items-center justify-center shadow-lg">
          <span className="text-4xl text-white font-bold">HD</span>
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-[#263238] mb-2">
            Health Desk AI
          </h2>
          <p className="text-[#455A64]">
            Book, view, or manage your appointments by voice
          </p>
        </div>

        {error && (
          <div className="w-full max-w-md">
            <Notification
              type="error"
              message={error}
              onDismiss={() => setError(null)}
            />
          </div>
        )}

        <Controls
          isConnected={false}
          onStartCall={startCall}
          onEndCall={() => {}}
        />
        {isConnecting && (
          <p className="text-sm text-[#B0BEC5]">Connecting...</p>
        )}
      </div>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={connectionState.url}
      token={connectionState.token}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={disconnect}
      onError={handleRoomError}
    >
      <RoomContent onDisconnect={disconnect} />
    </LiveKitRoom>
  );
}
