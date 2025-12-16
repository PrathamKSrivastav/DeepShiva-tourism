import { useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ChatWindow from "./components/ChatWindow";
import LoginButton from "./components/LoginButton";
import UserDropdown from "./components/UserDropdown";
import ChatHistorySidebar from "./components/ChatHistorySidebar";
import { fetchPersonas } from "./api";
import { useNavigate } from "react-router-dom"; 

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function AppContent() {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState("local_guide");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [darkMode, setDarkMode] = useState(true);
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [newChatTrigger, setNewChatTrigger] = useState(Date.now());
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate(); 

  useEffect(() => {
    fetchPersonas().then((d) => setPersonas(d.personas));
  }, []);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [darkMode]);

  useEffect(() => {
    const handleLogout = () => {
      console.log("🧹 Clearing chat sessions on logout");
      setChatSessions([]);
      setSelectedChat(null);
      setCurrentSessionId(null);
      setNewChatTrigger(Date.now());
    };

    window.addEventListener("user-logout", handleLogout);
    return () => window.removeEventListener("user-logout", handleLogout);
  }, []);

  const handlePersonaSwitch = (personaId, existingChat) => {
    console.log(`🔄 handlePersonaSwitch called:`, {
      personaId,
      existingChat: existingChat?._id,
    });
    setSelectedPersona(personaId);

    if (existingChat) {
      console.log(`✅ Loading existing chat: ${existingChat._id}`);
      setSelectedChat(existingChat);
      setCurrentSessionId(existingChat._id);
    } else {
      console.log(`✨ Starting fresh chat for ${personaId}`);
      setSelectedChat(null);
      setCurrentSessionId(null);
      setNewChatTrigger(Date.now());
    }
  };

  const handleSelectChatFromSidebar = (chat) => {
    if (chat) {
      console.log(`📖 Selected chat from sidebar: ${chat._id}`);
      setSelectedChat(chat);
      setCurrentSessionId(chat._id);
      if (chat.persona !== selectedPersona) {
        setSelectedPersona(chat.persona);
      }
    } else {
      setSelectedChat(null);
      setCurrentSessionId(null);
    }
  };

  return (
    <div
      className={`h-screen flex flex-col ${
        darkMode
          ? "bg-dark-bg text-slate-100"
          : "bg-gradient-to-br from-blue-50 to-indigo-100 text-gray-900"
      }`}
    >
      <header
        className={`h-20 border-b flex items-center px-6 justify-between flex-shrink-0 ${
          darkMode
            ? "bg-dark-surface border-dark-border"
            : "bg-white border-gray-200"
        }`}
      >
        <button
          className={`lg:hidden px-3 py-1 rounded-md transition ${
            darkMode
              ? "border-dark-border text-slate-200 bg-dark-elev hover:bg-dark-elev/80"
              : "border-gray-300 text-gray-700 bg-white/60"
          }`}
          onClick={() => setSidebarOpen(true)}
        >
          ☰
        </button>

        <img
          src="/header-icon.png"
          alt="Deep Shiva Tourism"
          className="h-14 w-auto rounded-lg"
        />

        <div className="flex items-center gap-4">
          <button
            onClick={() => setDarkMode((v) => !v)}
            className={`p-2 rounded-lg transition-colors ring-1 ${
              darkMode
                ? "bg-dark-elev ring-dark-border text-yellow-300 hover:bg-dark-elev/90"
                : "bg-white/80 ring-gray-200 text-gray-700 hover:bg-white"
            }`}
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {darkMode ? "☀️" : "🌙"}
          </button>

          <button
            onClick={() => navigate("/emergency")}
            className={`px-3 py-2 rounded-lg font-semibold transition-colors ring-1 flex items-center gap-2 ${
              darkMode
                ? "bg-dark-elev ring-dark-border text-emerald-300 hover:bg-dark-elev/90"
                : "bg-white/80 ring-gray-200 text-emerald-600 hover:bg-white"
            }`}
            title="View emergency helplines"
          >
            🆘 <span className="hidden sm:inline">Help</span>
          </button>

          {!isAuthenticated && <LoginButton darkMode={darkMode} />}
          {isAuthenticated && <UserDropdown darkMode={darkMode} />}
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 overflow-hidden">
        <div className="h-full max-w-[1920px] mx-auto px-4 py-4 lg:py-6">
          <div className="flex gap-4 lg:gap-6 h-full">
            {/* LEFT: History Sidebar */}
            <ChatHistorySidebar
              currentPersona={selectedPersona}
              selectedChatId={currentSessionId}
              onSelectChat={handleSelectChatFromSidebar}
              onNewChat={() => {
                setSelectedChat(null);
                setCurrentSessionId(null);
                setNewChatTrigger(Date.now());
              }}
              isOpen={sidebarOpen}
              onToggle={() => setSidebarOpen(false)}
              refreshTrigger={refreshTrigger}
              darkMode={darkMode}
              onSessionsUpdate={setChatSessions}
            />

            {/* CENTER: Chat Window (now takes full width) */}
            <div className="flex-1 min-w-0">
              <ChatWindow
                selectedPersona={selectedPersona}
                selectedChat={selectedChat}
                currentSessionId={currentSessionId}
                newChatTrigger={newChatTrigger}
                personas={personas}
                onPersonaChange={handlePersonaSwitch}
                onSessionCreated={setCurrentSessionId}
                onNewChatCreated={() => setRefreshTrigger((prev) => prev + 1)}
                darkMode={darkMode}
                chatSessions={chatSessions}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return <AppContent />;
}
