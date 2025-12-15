import { useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ChatWindow from "./components/ChatWindow";
import PersonaSelector from "./components/PersonaSelector";
import LoginButton from "./components/LoginButton";
import UserDropdown from "./components/UserDropdown";
import ChatHistorySidebar from "./components/ChatHistorySidebar";
import { fetchPersonas, createNewChatSession } from "./api";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function AppContent() {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState("local_guide");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [personaSelectorOpen, setPersonaSelectorOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    fetchPersonas().then((d) => setPersonas(d.personas));
  }, []);

return (
  <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
    {/* Header */}
    <header className="h-16 bg-white border-b flex items-center px-6 justify-between flex-shrink-0">
      <button
        className="lg:hidden px-3 py-1 border rounded"
        onClick={() => setSidebarOpen(true)}
      >
        History
      </button>
      <h1 className="font-bold text-lg">Deep Shiva Tourism</h1>

      <div className="flex items-center gap-3">
        {!isAuthenticated && <LoginButton />}
        {isAuthenticated && <UserDropdown />}
      </div>
    </header>

    {/* Main Layout - fills remaining space */}
    <main className="flex-1 overflow-hidden">
      <div className="h-full max-w-[1920px] mx-auto px-4 py-4 lg:py-6">
        <div className="flex gap-4 lg:gap-6 h-full">
          {/* LEFT: History Sidebar */}
          <ChatHistorySidebar
            currentPersona={selectedPersona}
            onSelectChat={setSelectedChat}
            onNewChat={() => setSelectedChat(null)}
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(false)}
            refreshTrigger={refreshTrigger}
          />

          {/* CENTER: Chat Window - flexible width */}
          <div className="flex-1 min-w-0">
            <ChatWindow
              selectedPersona={selectedPersona}
              selectedChat={selectedChat}
              personas={personas}
              onPersonaChange={setSelectedPersona}
              personaSelectorOpen={personaSelectorOpen}
              onPersonaSelectorToggle={setPersonaSelectorOpen}
            />
          </div>

          {/* RIGHT: Persona Selector - visible only on lg+ screens */}
          <div className="hidden lg:block w-80 xl:w-96 flex-shrink-0">
            <div className="h-full bg-white rounded-lg shadow-lg p-4 overflow-y-auto">
              <PersonaSelector
                personas={personas}
                selectedPersona={selectedPersona}
                onSelectPersona={setSelectedPersona}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
);
}

export default function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
