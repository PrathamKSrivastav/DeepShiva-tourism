import { useState, useEffect } from "react";
import { getChatHistory, deleteChat, updateSessionTitle } from "../api";
import { useAuth } from "../context/AuthContext";

function ChatHistorySidebar({
  currentPersona,
  onSelectChat,
  onNewChat,
  isOpen,
  onToggle,
  refreshTrigger,
  darkMode,
}) {
  const [chatSessions, setChatSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [renamingChatId, setRenamingChatId] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const { isAuthenticated } = useAuth();
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const checkSize = () => setIsDesktop(window.innerWidth >= 1024);
    checkSize();
    window.addEventListener("resize", checkSize);
    return () => window.removeEventListener("resize", checkSize);
  }, []);

  useEffect(() => {
    if (isAuthenticated) loadChatHistory();
    else {
      setChatSessions([]);
      setLoading(false);
    }
  }, [isAuthenticated, currentPersona, refreshTrigger]);

  const loadChatHistory = async () => {
    setLoading(true);
    try {
      const res = await getChatHistory(currentPersona, 50);
      const sessions = res.sessions || [];
      setChatSessions(sessions);

      if (sessions.length > 0) {
        setSelectedChatId(sessions[0]._id);
        onSelectChat(sessions[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChat = (chat) => {
    setSelectedChatId(chat._id);
    onSelectChat(chat);
    if (!isDesktop) onToggle();
  };

  const handleDeleteChat = async (chatId, e) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;

    try {
      await deleteChat(chatId);
      setChatSessions((prev) => prev.filter((c) => c._id !== chatId));
      if (selectedChatId === chatId) {
        setSelectedChatId(null);
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
      alert("Failed to delete conversation");
    }
  };

  const handleNewChat = () => {
    setSelectedChatId(null);
    onNewChat();
    if (!isDesktop) onToggle();
  };

  const handleSaveTitle = async (chatId) => {
    try {
      await updateSessionTitle(chatId, newTitle);
      setChatSessions((prev) =>
        prev.map((c) => (c._id === chatId ? { ...c, title: newTitle } : c))
      );
      setRenamingChatId(null);
    } catch (error) {
      console.error("Error updating title:", error);
      alert("Failed to update title");
    }
  };

  const SidebarContent = () => (
    <div
      className={`h-full flex flex-col ${
        darkMode
          ? "bg-dark-surface border-r border-dark-border"
          : "bg-white/40 backdrop-blur-xl border-white/20"
      }`}
    >
      {/* Glass Header */}
      <div
        className={`p-5 flex items-center justify-between border-b ${
          darkMode ? "border-dark-border" : "border-white/20"
        }`}
      >
        <h2
          className={`font-semibold tracking-tight ${
            darkMode ? "text-slate-100" : "text-gray-800"
          }`}
        >
          Your Journeys
        </h2>
        {!isDesktop && (
          <button
            onClick={onToggle}
            className={`p-1 rounded-full transition-colors ${
              darkMode
                ? "text-gray-400 hover:bg-dark-elev/60"
                : "text-gray-500 hover:bg-black/5"
            }`}
          >
            ✕
          </button>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          className={`w-full py-2.5 px-4 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition ${
            darkMode
              ? "bg-gradient-to-r from-accent-indigo to-accent-fuchsia text-white shadow-md hover:from-accent-indigo/95 hover:to-accent-fuchsia/95"
              : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-md"
          }`}
        >
          <span className="text-lg leading-none">+</span> Start New Chat
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2">
        {loading ? (
          <div className="flex justify-center py-10">
            <div
              className="w-6 h-6 border-2 rounded-full animate-spin"
              style={{
                borderColor: "transparent",
                borderTopColor: darkMode ? undefined : "#6366F1",
                borderLeftColor: darkMode ? "#6366F1" : undefined,
              }}
            />
          </div>
        ) : chatSessions.length === 0 ? (
          <div
            className={`text-center py-10 text-sm ${
              darkMode ? "text-dark-muted" : "text-gray-400"
            }`}
          >
            No past conversations
          </div>
        ) : (
          chatSessions.map((chat) => (
            <div
              key={chat._id}
              onClick={() => handleSelectChat(chat)}
              className={`group relative rounded-xl px-4 py-3 cursor-pointer transition-all duration-200 border-2 ${
                selectedChatId === chat._id
                  ? darkMode
                    ? "bg-gradient-to-r from-accent-indigo/12 to-accent-fuchsia/8 border-accent-indigo shadow-[0_8px_24px_rgba(99,102,241,0.06)]"
                    : "bg-indigo-100 border-indigo-500 shadow-md"
                  : darkMode
                  ? "bg-dark-surface/40 border-transparent hover:bg-dark-elev/60 hover:border-dark-border"
                  : "bg-white/30 border-transparent hover:bg-white/50 hover:border-white/30"
              }`}
            >
              {/* Active Indicator Line */}
              {selectedChatId === chat._id && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-gradient-to-b from-accent-indigo to-accent-fuchsia" />
              )}

              {renamingChatId === chat._id ? (
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onBlur={() => handleSaveTitle(chat._id)}
                  onKeyDown={(e) =>
                    e.key === "Enter" && handleSaveTitle(chat._id)
                  }
                  autoFocus
                  className={`w-full px-2 py-1 text-sm rounded focus:outline-none focus:ring-2 focus:ring-accent-indigo/30 border ${
                    darkMode
                      ? "bg-dark-elev text-slate-100 border-dark-border"
                      : "bg-white/80"
                  }`}
                />
              ) : (
                <div className="flex items-center justify-between pl-3">
                  <div className="flex-1 min-w-0 pr-2">
                    <p
                      className={`text-sm font-medium truncate ${
                        selectedChatId === chat._id
                          ? darkMode
                            ? "text-white"
                            : "text-indigo-900"
                          : darkMode
                          ? "text-slate-100"
                          : "text-gray-700"
                      }`}
                    >
                      {chat.title || "New Conversation"}
                    </p>
                    <p
                      className={`text-[10px] mt-0.5 truncate ${
                        darkMode ? "text-dark-muted" : "text-gray-500"
                      }`}
                    >
                      {new Date(chat.updated_at).toLocaleDateString()} •{" "}
                      {chat.persona || "Guide"}
                    </p>
                  </div>

                  {/* Hover Actions */}
                  <div
                    className={`flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${
                      selectedChatId === chat._id ? "opacity-100" : ""
                    }`}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setRenamingChatId(chat._id);
                        setNewTitle(chat.title || "");
                      }}
                      className={`p-1 rounded transition-colors ${
                        darkMode
                          ? "text-dark-muted hover:bg-dark-elev/50 hover:text-accent-fuchsia"
                          : "text-gray-400 hover:bg-indigo-50 hover:text-indigo-600"
                      }`}
                    >
                      ✎
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteChat(chat._id, e);
                      }}
                      className={`p-1 rounded transition-colors ${
                        darkMode
                          ? "text-dark-muted hover:bg-red-900/40 hover:text-rose-300"
                          : "text-gray-400 hover:bg-red-50 hover:text-red-600"
                      }`}
                    >
                      🗑
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );

  /* Desktop View */
  if (isDesktop) {
    return (
      <aside className="w-72 h-full flex-shrink-0 relative z-10">
        <SidebarContent />
      </aside>
    );
  }

  /* Mobile Overlay */
  return (
    <>
      <div
        className={`fixed inset-0 z-40 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        style={{
          backgroundColor: isOpen ? "rgba(0, 0, 0, 0.4)" : "transparent",
          backdropFilter: isOpen ? "blur(4px)" : "none",
        }}
        onClick={onToggle}
      />
      <div
        className={`fixed left-0 top-0 h-full w-72 z-50 transform transition-transform duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] shadow-2xl ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <SidebarContent />
      </div>
    </>
  );
}

export default ChatHistorySidebar;
