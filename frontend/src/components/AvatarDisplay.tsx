import {
  useVoiceAssistant,
  BarVisualizer,
  useTracks,
  VideoTrack,
} from "@livekit/components-react";
import { Track } from "livekit-client";

export function AvatarDisplay() {
  const { state, audioTrack } = useVoiceAssistant();
  const tracks = useTracks([Track.Source.Camera]);

  const avatarTrack = tracks.find(
    (t) =>
      t.participant.identity.includes("simli") ||
      t.participant.identity.includes("avatar") ||
      t.participant.identity.includes("bey")
  );

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="w-64 h-64 rounded-2xl overflow-hidden bg-gradient-to-br from-[#EEF2F7] to-[#E0E5EB] flex items-center justify-center shadow-md">
        {avatarTrack ? (
          <VideoTrack
            trackRef={avatarTrack}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-[#034C81] flex items-center justify-center shadow-lg">
              <span className="text-3xl text-white font-bold">HD</span>
            </div>
            <BarVisualizer
              state={state}
              barCount={5}
              track={audioTrack}
              className="h-12"
            />
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            state === "speaking"
              ? "bg-[#4CAF50] animate-pulse"
              : state === "thinking"
              ? "bg-[#FFA726] animate-pulse"
              : state === "listening"
              ? "bg-[#2CA3FA]"
              : "bg-[#B0BEC5]"
          }`}
        />
        <span className="text-sm text-[#455A64] capitalize">{state}</span>
      </div>
    </div>
  );
}
