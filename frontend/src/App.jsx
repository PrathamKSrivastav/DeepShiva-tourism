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
  const [darkMode, setDarkMode] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    fetchPersonas().then((d) => setPersonas(d.personas));
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <div
      className={`h-screen flex flex-col ${
        darkMode
          ? "bg-gray-900"
          : "bg-gradient-to-br from-blue-50 to-indigo-100"
      }`}
    >
      {/* Header */}
      <header
        className={`h-16 ${
          darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"
        } border-b flex items-center px-6 justify-between flex-shrink-0`}
      >
        <button
          className={`lg:hidden px-3 py-1 border rounded ${
            darkMode
              ? "border-gray-600 text-gray-300"
              : "border-gray-300 text-gray-700"
          }`}
          onClick={() => setSidebarOpen(true)}
        >
          History
        </button>
        <h1
          className={`font-bold text-lg ${
            darkMode ? "text-white" : "text-gray-900"
          }`}
        >
          Deep Shiva Tourism
        </h1>

        <div className="flex items-center gap-4">
          {/* Dark Mode Toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`p-2 rounded-lg transition-colors ${
              darkMode
                ? "bg-gray-700 text-yellow-400 hover:bg-gray-600"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {darkMode ? "☀️" : "🌙"}
          </button>

          {!isAuthenticated && <LoginButton />}
          {isAuthenticated && <UserDropdown darkMode={darkMode} />}
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 overflow-hidden">
        <div
          className={`h-full max-w-[1920px] mx-auto px-4 py-4 lg:py-6 ${
            darkMode ? "bg-gray-900" : ""
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
                personaSelectorOpen={personaSelectorOpen}
                onPersonaSelectorToggle={setPersonaSelectorOpen}
                onNewChatCreated={() => setRefreshTrigger((prev) => prev + 1)}
                darkMode={darkMode}
              />
            </div>

            {/* RIGHT: Persona Selector */}
            <div
              className={`hidden lg:block w-80 xl:w-96 flex-shrink-0 ${
                darkMode
                  ? "bg-gray-800 rounded-lg shadow-lg p-4 overflow-y-auto"
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
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
