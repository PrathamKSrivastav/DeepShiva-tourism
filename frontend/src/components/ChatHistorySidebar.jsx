import { useState, useEffect } from "react";
import { getChatHistory, deleteChat, updateSessionTitle } from "../api";
import { useAuth } from "../context/AuthContext";
import PdfExportButton from "./PdfExportButton"; // ← ADDED

import { useSummaryGenerator } from "../hooks/useSummaryGenerator";
import SummaryModal from "./SummaryModal";
import SummaryButton from "./SummaryButton";

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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState(null);
  const { isAuthenticated } = useAuth();
  const [isDesktop, setIsDesktop] = useState(true);
  

  const {
  isGenerating: isGeneratingSummary,
  isDownloading: isDownloadingSummary,
  error: summaryError,
  summary,
  generateSummary,
  downloadSummaryPdf,
  clearSummary,
  } = useSummaryGenerator();

const [showSummaryModal, setShowSummaryModal] = useState(false);
const [selectedSessionForSummary, setSelectedSessionForSummary] = useState(null);
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

  const handleDeleteClick = (chat, e) => {
    e.stopPropagation();
    setChatToDelete(chat);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!chatToDelete) return;

    try {
      await deleteChat(chatToDelete._id);
      setChatSessions((prev) => prev.filter((c) => c._id !== chatToDelete._id));
      if (selectedChatId === chatToDelete._id) {
        setSelectedChatId(null);
      }
      setDeleteDialogOpen(false);
      setChatToDelete(null);
    } catch (error) {
      console.error("Error deleting chat:", error);
      alert("Failed to delete conversation");
    }
  };

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setChatToDelete(null);
  };

  const handleNewChat = async () => {
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
  


  const handleGenerateSummary = async (chat, e) => {
  e.stopPropagation();
  setSelectedSessionForSummary(chat);
  setShowSummaryModal(true);
  
  try {
    await generateSummary(chat._id);
  } catch (error) {
    console.error('Failed to generate summary:', error);
  }
};

const handleDownloadSummary = async () => {
  if (!selectedSessionForSummary) return;

  try {
    await downloadSummaryPdf(
      selectedSessionForSummary._id,
      selectedSessionForSummary.title || 'chat'
    );
  } catch (error) {
    console.error('Failed to download summary:', error);
  }
};

const handleCloseSummaryModal = () => {
  setShowSummaryModal(false);
  setSelectedSessionForSummary(null);
  clearSummary();
};



  const SidebarContent = () => (
    <div
      className={`flex flex-col h-full ${
        darkMode ? "bg-gray-900" : "bg-gray-50"
      }`}
    >
      {/* Header */}
      <div
        className={`p-4 border-b ${
          darkMode ? "border-gray-700" : "border-gray-200"
        }`}
      >
        <h2
          className={`text-lg font-bold ${
            darkMode ? "text-white" : "text-gray-800"
          }`}
        >
          Chat History
        </h2>
        <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
          {chatSessions.length} conversation{chatSessions.length !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500" />
          </div>
        ) : chatSessions.length === 0 ? (
          <div className="text-center py-12 px-4">
            <div className="text-4xl mb-3">💬</div>
            <p
              className={`text-sm ${
                darkMode ? "text-gray-400" : "text-gray-500"
              }`}
            >
              No conversations yet
            </p>
          </div>
        ) : (
          chatSessions.map((chat) => (
            <div
              key={chat._id}
              className={`group relative p-3 rounded-lg cursor-pointer transition-all ${
                selectedChatId === chat._id
                  ? darkMode
                    ? "bg-teal-900/30 border-2 border-teal-500"
                    : "bg-teal-50 border-2 border-teal-500"
                  : darkMode
                  ? "bg-gray-800 hover:bg-gray-750 border-2 border-transparent"
                  : "bg-white hover:bg-gray-100 border-2 border-transparent"
              }`}
            >
              {renamingChatId === chat._id ? (
                <div className="flex flex-col gap-2" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    className={`px-2 py-1 text-sm border rounded ${
                      darkMode
                        ? "bg-gray-700 border-gray-600 text-white"
                        : "bg-white border-gray-300 text-gray-900"
                    } focus:outline-none focus:ring-2 focus:ring-teal-500`}
                    placeholder="New title"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveTitle(chat._id)}
                      className="flex-1 px-2 py-1 bg-teal-500 text-white text-xs rounded hover:bg-teal-600"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setRenamingChatId(null)}
                      className={`flex-1 px-2 py-1 text-xs rounded ${
                        darkMode
                          ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div onClick={() => handleSelectChat(chat)}>
                    <h3
                      className={`font-medium line-clamp-1 ${
                        darkMode ? "text-white" : "text-gray-800"
                      }`}
                    >
                      {chat.title || "New Conversation"}
                    </h3>
                    <p
                      className={`text-xs mt-1 ${
                        darkMode ? "text-gray-400" : "text-gray-500"
                      }`}
                    >
                      {new Date(chat.updated_at).toLocaleDateString()} •{" "}
                      {chat.persona || "Guide"}
                    </p>
                  </div>

                  {/* ✨ ACTION BUTTONS - ADDED ✨ */}
                  <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* PDF Export Button */}
                    <div onClick={(e) => e.stopPropagation()}>
                      <PdfExportButton
                        sessionId={chat._id}
                        sessionTitle={chat.title || "Chat"}
                        variant="icon"
                        darkMode={darkMode}
                        className="shadow-sm"
                      />
                    </div>
                     
                      {/* ✨ NEW: AI Summary Button ✨ */}
  <div onClick={(e) => e.stopPropagation()}>
    <SummaryButton
      onClick={(e) => handleGenerateSummary(chat, e)}
      variant="icon"
      disabled={!chat.messages || chat.messages.length < 2}
    />
  </div>    


                    {/* Edit Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setRenamingChatId(chat._id);
                        setNewTitle(chat.title || "");
                      }}
                      className={`p-1.5 rounded transition-colors ${
                        darkMode
                          ? "bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600"
                          : "bg-white text-gray-600 hover:bg-gray-100 border border-gray-200"
                      }`}
                      title="Rename chat"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                        />
                      </svg>
                    </button>

                    {/* Delete Button */}
                    <button
<<<<<<< HEAD
                      onClick={(e) => handleDeleteChat(chat._id, e)}
                      className={`p-1.5 rounded transition-colors ${
                        darkMode
                          ? "bg-gray-700 text-red-400 hover:bg-red-900/30 border border-gray-600"
                          : "bg-white text-red-600 hover:bg-red-50 border border-gray-200"
=======
                      onClick={(e) => handleDeleteClick(chat, e)}
                      className={`p-1 rounded transition-colors ${
                        darkMode
                          ? "text-dark-muted hover:bg-dark-elev/50 hover:text-red-400"
                          : "text-gray-400 hover:bg-red-50 hover:text-red-600"
>>>>>>> c62f8f4b36b7433f42a95a6c647a5cdcd8fad877
                      }`}
                      title="Delete chat"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* New Chat Button */}
      <div
        className={`p-4 border-t ${
          darkMode ? "border-gray-700" : "border-gray-200"
        }`}
      >
        <button
          onClick={handleNewChat}
          className="w-full px-4 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium flex items-center justify-center gap-2 shadow-md"
        >
          <svg
            className="h-5 w-5"
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
          New Chat
        </button>
      </div>
    </div>
  );

<<<<<<< HEAD
  // Mobile/Desktop rendering logic
  if (!isDesktop) {
    return (
      <>
        {isOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={onToggle}
          />
        )}
        <div
          className={`fixed top-0 left-0 h-full w-80 z-50 transform transition-transform duration-300 lg:hidden ${
            isOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <SidebarContent />
        </div>
      
      <SummaryModal
          isOpen={showSummaryModal}
          onClose={handleCloseSummaryModal}
          summary={summary}
          isGenerating={isGeneratingSummary}
          error={summaryError}
          onDownloadPdf={handleDownloadSummary}
          isDownloading={isDownloadingSummary}
        
        
        
        
        />
      </>
=======
  /* Delete Confirmation Dialog */
  const DeleteDialog = () => (
    <>
      {/* Overlay */}
      <div
        className={`fixed inset-0 z-[60] transition-opacity duration-200 ${
          deleteDialogOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        style={{
          backgroundColor: deleteDialogOpen
            ? darkMode
              ? "rgba(0, 0, 0, 0.7)"
              : "rgba(0, 0, 0, 0.5)"
            : "transparent",
          backdropFilter: deleteDialogOpen ? "blur(4px)" : "none",
        }}
        onClick={cancelDelete}
      />

      {/* Dialog */}
      <div
        className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[70] transform transition-all duration-200 ${
          deleteDialogOpen
            ? "scale-100 opacity-100"
            : "scale-95 opacity-0 pointer-events-none"
        }`}
      >
        <div
          className={`rounded-2xl shadow-2xl border ${
            darkMode
              ? "bg-dark-surface border-dark-border"
              : "bg-white border-gray-200"
          } p-6 max-w-sm w-full mx-4`}
        >
          {/* Icon */}
          <div className="flex justify-center mb-4">
            <div
              className={`w-14 h-14 rounded-full flex items-center justify-center text-2xl ${
                darkMode
                  ? "bg-red-500/10 text-red-400"
                  : "bg-red-100 text-red-600"
              }`}
            >
              ⚠️
            </div>
          </div>

          {/* Title */}
          <h3
            className={`text-lg font-semibold text-center mb-2 ${
              darkMode ? "text-white" : "text-gray-900"
            }`}
          >
            Delete Conversation?
          </h3>

          {/* Message */}
          <p
            className={`text-sm text-center mb-6 ${
              darkMode ? "text-gray-400" : "text-gray-600"
            }`}
          >
            {chatToDelete && (
              <>
                Are you sure you want to delete "
                <span className="font-semibold">
                  {chatToDelete.title || "New Conversation"}
                </span>
                "? This action cannot be undone.
              </>
            )}
          </p>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              onClick={cancelDelete}
              className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all ${
                darkMode
                  ? "bg-dark-elev text-slate-100 hover:bg-dark-elev/80 border border-dark-border"
                  : "bg-gray-100 text-gray-900 hover:bg-gray-200 border border-gray-200"
              }`}
            >
              Cancel
            </button>
            <button
              onClick={confirmDelete}
              className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all ${
                darkMode
                  ? "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-900/20"
                  : "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-600/20"
              }`}
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </>
  );

  /* Desktop View */
  if (isDesktop) {
    return (
      <aside className="w-72 h-full flex-shrink-0 relative z-10">
        <SidebarContent />
        <DeleteDialog />
      </aside>
>>>>>>> c62f8f4b36b7433f42a95a6c647a5cdcd8fad877
    );
  }

  return (
    <div className="w-80 border-r h-screen">
      <SidebarContent />

      {/* ✨ ADD SUMMARY MODAL HERE ✨ */}
      <SummaryModal
        isOpen={showSummaryModal}
        onClose={handleCloseSummaryModal}
        summary={summary}
        isGenerating={isGeneratingSummary}
        error={summaryError}
        onDownloadPdf={handleDownloadSummary}
        isDownloading={isDownloadingSummary}
      />
<<<<<<< HEAD

    </div>
=======
      <div
        className={`fixed left-0 top-0 h-full w-72 z-50 transform transition-transform duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] shadow-2xl ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <SidebarContent />
      </div>
      <DeleteDialog />
    </>
>>>>>>> c62f8f4b36b7433f42a95a6c647a5cdcd8fad877
  );
}

export default ChatHistorySidebar;
