import { useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ChatWindow from "./components/ChatWindow";
import PersonaSelector from "./components/PersonaSelector";
import LoginButton from "./components/LoginButton";
import UserDropdown from "./components/UserDropdown";
import ChatHistorySidebar from "./components/ChatHistorySidebar";
import { fetchPersonas } from "./api";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function AppContent() {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState("local_guide");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [darkMode, setDarkMode] = useState(true); // default to polished dark
  const { isAuthenticated } = useAuth();

useEffect(() => {
}, [isAuthenticated]);

  useEffect(() => {
    fetchPersonas().then((d) => setPersonas(d.personas));
  }, []);

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  }, [darkMode]);

  return (
    <div
      className={`h-screen flex flex-col ${
        darkMode
          ? "bg-dark-bg text-slate-100"
          : "bg-gradient-to-br from-blue-50 to-indigo-100 text-gray-900"
      }`}
    >
      {/* Header */}
      <header
        className={`h-16 border-b flex items-center px-6 justify-between flex-shrink-0 ${
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
          History
        </button>

        <h1 className="font-heading font-semibold text-lg tracking-tight">
          Deep Shiva Tourism
        </h1>

        <div className="flex items-center gap-4">
          {/* Dark Mode Toggle */}
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

          {!isAuthenticated && <LoginButton darkMode={darkMode} />}
          {isAuthenticated && <UserDropdown darkMode={darkMode} />}
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 overflow-hidden">
        <div
          className={`h-full max-w-[1920px] mx-auto px-4 py-4 lg:py-6 ${
            darkMode ? "" : ""
          }`}
        >
          <div className="flex gap-4 lg:gap-6 h-full">
            {/* LEFT: History Sidebar */}
            <ChatHistorySidebar
              currentPersona={selectedPersona}
              onSelectChat={setSelectedChat}
              onNewChat={() => setSelectedChat(null)}
              isOpen={sidebarOpen}
              onToggle={() => setSidebarOpen(false)}
              refreshTrigger={refreshTrigger}
              darkMode={darkMode}
            />

            {/* CENTER: Chat Window */}
            <div className="flex-1 min-w-0">
              <ChatWindow
                selectedPersona={selectedPersona}
                selectedChat={selectedChat}
                personas={personas}
                onPersonaChange={setSelectedPersona}
                onNewChatCreated={() => setRefreshTrigger((prev) => prev + 1)}
                darkMode={darkMode}
              />
            </div>

            {/* RIGHT: Persona Selector */}
            <div
              className={`hidden lg:block w-80 xl:w-96 flex-shrink-0 ${
                darkMode
                  ? "bg-dark-surface rounded-lg shadow-lg p-4 overflow-y-auto border border-dark-border"
                  : "bg-white rounded-lg shadow-lg p-4 overflow-y-auto"
              }`}
            >
              <PersonaSelector
                personas={personas}
                selectedPersona={selectedPersona}
                onSelectPersona={setSelectedPersona}
                darkMode={darkMode}
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

