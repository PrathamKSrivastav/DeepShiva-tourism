import { useState, useEffect } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ChatWindow from "./components/ChatWindow";
import PersonaSelector from "./components/PersonaSelector";
import LoginButton from "./components/LoginButton";
import UserDropdown from "./components/UserDropdown";
import ConnectionStatus from "./components/ConnectionStatus";
import ChatHistorySidebar from "./components/ChatHistorySidebar";
import { fetchPersonas, createNewChatSession } from "./api";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

function AppContent() {
  const [personas, setPersonas] = useState([]);
  const [selectedPersona, setSelectedPersona] = useState("local_guide");
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedChat, setSelectedChat] = useState(null);
  const [newChatTrigger, setNewChatTrigger] = useState(0);
  const { isAuthenticated, user, loading: authLoading } = useAuth();
  const [currentSessionId, setCurrentSessionId] = useState(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  const loadPersonas = async () => {
    try {
      const data = await fetchPersonas();
      setPersonas(data.personas);
      setLoading(false);
    } catch (error) {
      console.error("Error loading personas:", error);
      setLoading(false);
    }
  };

  const handleSelectChat = (chat) => {
    console.log("📖 Switching to chat:", chat._id);
    setSelectedChat(chat);
    setCurrentSessionId(chat._id);
    setSelectedPersona(chat.persona);
  };

  const handleNewChat = async () => {
    console.log("🆕 Creating new chat...");
    setSelectedChat(null);
    setCurrentSessionId(null);
    setNewChatTrigger((prev) => prev + 1);

    // Create new session if authenticated
    if (isAuthenticated) {
      try {
        const newSession = await createNewChatSession(selectedPersona);
        console.log("✅ New session created:", newSession.session_id);
        setCurrentSessionId(newSession.session_id);
      } catch (error) {
        console.error("❌ Error creating session:", error);
      }
    }
  };

  const handleSessionCreated = (sessionId) => {
    console.log("📝 Session created from chat:", sessionId);
    setCurrentSessionId(sessionId);
  };

  const selectedPersonaInfo = personas.find((p) => p.id === selectedPersona);

  if (loading || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Deep Shiva...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🏔️</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Deep Shiva Tourism
                </h1>
                <p className="text-sm text-gray-500">
                  Your AI Guide to Uttarakhand
                </p>
              </div>
            </div>

            {/* Right Side Controls */}
            <div className="flex items-center space-x-4">
              {/* History Toggle Button */}
              {isAuthenticated && (
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors relative"
                  title="Chat History"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  {sidebarOpen && (
                    <span className="absolute top-0 right-0 w-2 h-2 bg-indigo-600 rounded-full"></span>
                  )}
                </button>
              )}

              <ConnectionStatus />

              {isAuthenticated ? (
                <UserDropdown />
              ) : (
                <LoginButton
                  onSuccess={() => console.log("Login successful")}
                />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Persona Selector */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-6 sticky top-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Choose Your Guide
              </h2>
              <PersonaSelector
                personas={personas}
                selectedPersona={selectedPersona}
                onSelectPersona={(personaId) => {
                  console.log("🎭 Persona changed to:", personaId);
                  setSelectedPersona(personaId);
                  setSelectedChat(null);
                  setCurrentSessionId(null); // Clear session when switching persona
                  setNewChatTrigger((prev) => prev + 1); // Reset chat window
                }}
              />

              {/* Auth Status Info */}
              {!isAuthenticated && (
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-xs text-blue-800 mb-2">
                    <strong>💡 Tip:</strong> Sign in to save your chat history!
                  </p>
                  <p className="text-xs text-blue-600">
                    Chat works without login, but conversations won't be saved.
                  </p>
                </div>
              )}

              {isAuthenticated && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-xs text-green-800">
                    ✅ Your chats are being saved automatically
                  </p>
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="mt-2 text-xs text-green-700 hover:text-green-900 font-medium flex items-center space-x-1"
                  >
                    <span>📜</span>
                    <span>View chat history</span>
                  </button>
                </div>
              )}

              {/* Tip Box */}
              <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                <p className="text-xs text-gray-700">
                  <strong>💡 Tip:</strong> Each guide offers a unique
                  perspective. Switch personas to get different insights about
                  the same topic!
                </p>
              </div>
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-3">
            <ChatWindow
              selectedPersona={selectedPersona}
              personaInfo={selectedPersonaInfo}
              selectedChat={selectedChat}
              newChatTrigger={newChatTrigger}
              currentSessionId={currentSessionId}
              onSessionCreated={handleSessionCreated}
            />
          </div>
        </div>
      </main>

      {/* Chat History Sidebar */}
      <ChatHistorySidebar
        currentPersona={selectedPersona}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentSessionId={currentSessionId}
      />

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-600">
            <p>Deep Shiva Tourism AI • Powered by RAG & Groq API</p>
            <p className="mt-1">
              {isAuthenticated && user && (
                <span className="text-green-600">
                  Welcome back, {user.name}! 👋
                </span>
              )}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
