import { useState, useEffect } from "react";
import { getChatHistory, deleteChat } from "../api";
import { useAuth } from "../context/AuthContext";

function ChatHistorySidebar({
  currentPersona,
  onSelectChat,
  onNewChat,
  isOpen,
  onToggle,
  refreshTrigger, // ADD THIS LINE
}) {
  const [chatSessions, setChatSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadChatHistory();
    }
  }, [isAuthenticated, currentPersona, refreshTrigger]);

  const loadChatHistory = async () => {
    setLoading(true);
    try {
      const response = await getChatHistory(currentPersona, 50);
      setChatSessions(response.sessions || []); // Changed from .chats to .sessions
    } catch (error) {
      console.error("Error loading chat history:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChat = (chat) => {
    setSelectedChatId(chat._id);
    onSelectChat(chat);
  };

  const handleDeleteChat = async (chatId, e) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;

    try {
      await deleteChat(chatId);
      setChatSessions((prev) => prev.filter((chat) => chat._id !== chatId));
      if (selectedChatId === chatId) {
        onNewChat();
        setSelectedChatId(null);
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
      alert("Failed to delete chat");
    }
  };

  const handleNewChat = () => {
    setSelectedChatId(null);
    onNewChat();
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getChatPreview = (chat) => {
    const userMessages = chat.messages.filter((m) => m.role === "user");
    if (userMessages.length === 0) return "New conversation";
    return (
      userMessages[0].content.slice(0, 50) +
      (userMessages[0].content.length > 50 ? "..." : "")
    );
  };

  const getPersonaIcon = (persona) => {
    const icons = {
      local_guide: "🧑‍🤝‍🧑",
      spiritual_teacher: "🕉️",
      trek_companion: "🏔️",
      cultural_expert: "📚",
    };
    return icons[persona] || "🤖";
  };

  if (!isAuthenticated) {
    return (
      <div
        className={`fixed right-0 top-0 h-full bg-white shadow-lg border-l border-gray-200 transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        } w-80 z-40`}
      >
        <div className="p-6 h-full flex flex-col items-center justify-center text-center">
          <div className="text-6xl mb-4">🔒</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Sign in to view history
          </h3>
          <p className="text-sm text-gray-600">
            Login with Google to save and access your chat history across
            devices
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`fixed right-0 top-0 h-full bg-white shadow-lg border-l border-gray-200 transition-transform duration-300 ${
        isOpen ? "translate-x-0" : "translate-x-full"
      } w-80 z-40`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-indigo-50 to-purple-50">
        <h2 className="text-lg font-semibold text-gray-900">Chat History</h2>
        <button
          onClick={onToggle}
          className="p-2 hover:bg-white rounded-lg transition-colors"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={handleNewChat}
          className="w-full py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center justify-center space-x-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span>New Chat</span>
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : chatSessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">💬</div>
            <p className="text-sm">No chat history yet</p>
            <p className="text-xs mt-1">Start a conversation!</p>
          </div>
        ) : (
          chatSessions.map((chat) => (
            <div
              key={chat._id}
              onClick={() => handleSelectChat(chat)}
              className={`p-3 rounded-lg cursor-pointer transition-all hover:bg-gray-50 border ${
                selectedChatId === chat._id
                  ? "bg-indigo-50 border-indigo-200"
                  : "bg-white border-gray-200"
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <div className="flex items-center space-x-2 flex-1 min-w-0">
                  <span className="text-lg">
                    {getPersonaIcon(chat.persona)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {getChatPreview(chat)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteChat(chat._id, e)}
                  className="ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                <span>{formatDate(chat.updated_at)}</span>
                <span>{chat.messages.length} messages</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-600 text-center">
          {chatSessions.length} conversation
          {chatSessions.length !== 1 ? "s" : ""} saved
        </p>
      </div>
    </div>
  );
}

export default ChatHistorySidebar;
