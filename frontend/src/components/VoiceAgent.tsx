import { useState, useCallback } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { fetchToken } from "../services/api";
import { AvatarDisplay } from "./AvatarDisplay";
import { ToolStatusPanel } from "./ToolStatusPanel";
import { TranscriptPanel } from "./TranscriptPanel";
import { CallSummary } from "./CallSummary";
import { Controls } from "./Controls";

function RoomContent({ onDisconnect }: { onDisconnect: () => void }) {
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();

  const toggleMic = useCallback(async () => {
    await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  }, [localParticipant, isMicrophoneEnabled]);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex flex-col items-center gap-4">
          <AvatarDisplay />
        </div>
        <div className="flex flex-col gap-4">
          <TranscriptPanel />
          <ToolStatusPanel />
        </div>
      </div>
      <Controls
        isConnected={true}
        isMuted={!isMicrophoneEnabled}
        onStartCall={() => {}}
        onEndCall={onDisconnect}
        onToggleMic={toggleMic}
      />
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

  const startCall = useCallback(async () => {
    setIsConnecting(true);
    try {
      const identity = `patient-${Date.now()}`;
      const { token, url } = await fetchToken(identity);
      setConnectionState({ token, url });
    } catch (err) {
      console.error("Failed to connect:", err);
      alert("Failed to start call. Is the backend running?");
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
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
        <Controls
          isConnected={false}
          isMuted={false}
          onStartCall={startCall}
          onEndCall={() => {}}
          onToggleMic={() => {}}
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
    >
      <RoomContent onDisconnect={disconnect} />
    </LiveKitRoom>
  );
}
