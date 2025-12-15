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
      setChatSessions(res.sessions || []);
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

  const handleSaveTitle = async (chatId) => {
    if (!newTitle.trim()) {
      setRenamingChatId(null);
      return;
    }
    try {
      await updateSessionTitle(chatId, newTitle);
      setChatSessions((prev) =>
        prev.map((c) => (c._id === chatId ? { ...c, title: newTitle } : c))
      );
      setRenamingChatId(null);
    } catch (error) {
      console.error("Error updating title:", error);
    }
  };

  const handleNewChat = () => {
    setSelectedChatId(null);
    onNewChat();
    if (!isDesktop) onToggle();
  };

  const SidebarContent = () => (
    <div className="h-full flex flex-col bg-white/50 backdrop-blur-xl border-r border-white/20">
      {/* Header */}
      <div className="p-5 border-b border-white/20 flex items-center justify-between">
        <h2 className="font-semibold text-gray-800 tracking-tight">History</h2>
        {!isDesktop && (
          <button
            onClick={onToggle}
            className="text-gray-500 p-1 hover:bg-black/5 rounded-full"
          >
            ✕
          </button>
        )}
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          className="w-full py-2.5 px-4 bg-gray-900 text-white rounded-xl shadow-lg shadow-gray-200/50 hover:bg-gray-800 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 font-medium text-sm flex items-center justify-center gap-2"
        >
          <span>+</span> Start New Chat
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-1">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : chatSessions.length === 0 ? (
          <div className="text-center text-gray-400 py-10 text-sm">
            No past conversations
          </div>
        ) : (
          chatSessions.map((chat) => (
            <div
              key={chat._id}
              onClick={() => handleSelectChat(chat)}
              className={`group relative rounded-lg px-3 py-2.5 cursor-pointer transition-all duration-200 border border-transparent
                ${
                  selectedChatId === chat._id
                    ? "bg-white/80 shadow-sm border-white/40"
                    : "hover:bg-white/40"
                }`}
            >
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
                  className="w-full bg-white border border-indigo-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 pr-2">
                    <p
                      className={`text-sm font-medium truncate ${
                        selectedChatId === chat._id
                          ? "text-gray-900"
                          : "text-gray-700"
                      }`}
                    >
                      {chat.title || "New Conversation"}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5 truncate">
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
                      className="p-1 hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 rounded"
                    >
                      ✎
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat._id);
                      }}
                      className="p-1 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded"
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
      <aside className="w-72 h-full flex-shrink-0">
        <SidebarContent />
      </aside>
    );
  }

  /* Mobile Overlay */
  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-gray-900/20 backdrop-blur-sm transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
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
