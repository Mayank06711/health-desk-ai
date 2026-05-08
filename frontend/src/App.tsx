import { VoiceAgent } from "./components/VoiceAgent";

function App() {
  return (
    <div className="min-h-screen bg-[#F5F7FA]">
      <header className="bg-white border-b border-[#EEF2F7] px-6 py-4 shadow-sm">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#034C81] flex items-center justify-center">
            <span className="text-sm text-white font-bold">H</span>
          </div>
          <h1 className="text-lg font-semibold text-[#263238]">
            Health Desk AI
          </h1>
        </div>
      </header>
      <main className="p-6 max-w-5xl mx-auto">
        <VoiceAgent />
      </main>
    </div>
  );
}

export default App;
