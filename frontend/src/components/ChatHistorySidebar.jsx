import { useState, useEffect, useRef } from "react";
import { getChatHistory, deleteChat, updateSessionTitle } from "../api";
import { useAuth } from "../context/AuthContext";
import { useSummaryGenerator } from "../hooks/useSummaryGenerator";
import SummaryModal from "./SummaryModal";
import { usePdfExport } from "../hooks/usePdfExport";

function ChatHistorySidebar({
  currentPersona,
  onSelectChat,
  onNewChat,
  isOpen,
  onToggle,
  refreshTrigger,
  darkMode,
  onSessionsUpdate,
  selectedChatId,
}) {
  const [chatSessions, setChatSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [renamingChatId, setRenamingChatId] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState(null);
  const [openMenuId, setOpenMenuId] = useState(null);
  const { isAuthenticated } = useAuth();
  const [isDesktop, setIsDesktop] = useState(true);

  // Summary hooks
  const {
    summary,
    isGenerating: isSummaryGenerating,
    isDownloading: isPdfLoading,
    error: summaryError,
    generateSummary,
    downloadSummaryPdf,
  } = useSummaryGenerator();

  // PDF Export hook
  const {
    isLoading: isPdfExporting,
    error: pdfError,
    downloadPdf,
  } = usePdfExport();

  const [summaryModalOpen, setSummaryModalOpen] = useState(false);
  const [summarySessionId, setSummarySessionId] = useState(null);

  useEffect(() => {
    const checkSize = () => setIsDesktop(window.innerWidth >= 1024);
    checkSize();
    window.addEventListener("resize", checkSize);
    return () => window.removeEventListener("resize", checkSize);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadChatHistory();
    } else {
      setChatSessions([]);
      setLoading(false);
    }
  }, [isAuthenticated, currentPersona, refreshTrigger]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (openMenuId && !e.target.closest(".dropdown-menu")) {
        setOpenMenuId(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openMenuId]);

  // Show PDF export error as alert
  useEffect(() => {
    if (pdfError) {
      alert(`PDF Export Error: ${pdfError}`);
    }
  }, [pdfError]);

  const loadChatHistory = async () => {
    setLoading(true);
    try {
      const res = await getChatHistory(currentPersona, 50);
      const sessions = res.sessions || [];
      setChatSessions(sessions);

      if (onSessionsUpdate) {
        onSessionsUpdate(sessions);
      }

      console.log(
        `📚 Loaded ${sessions.length} sessions for ${currentPersona}`
      );
    } catch (e) {
      console.error("Error loading chat history:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChat = (chat) => {
    console.log(`📖 Sidebar selected chat: ${chat._id}`);
    onSelectChat(chat);
    if (!isDesktop) onToggle();
  };

  const handleDeleteClick = (chat, e) => {
    e.stopPropagation();
    setChatToDelete(chat);
    setDeleteDialogOpen(true);
    setOpenMenuId(null);
  };

  const confirmDelete = async () => {
    if (!chatToDelete) return;

    try {
      await deleteChat(chatToDelete._id);
      setChatSessions((prev) => prev.filter((c) => c._id !== chatToDelete._id));

      if (selectedChatId === chatToDelete._id) {
        console.log("🗑️ Deleted currently selected chat, clearing selection");
        onSelectChat(null);

        window.dispatchEvent(
          new CustomEvent("chat-deleted", {
            detail: { chatId: chatToDelete._id },
          })
        );
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
    console.log("✨ New chat button clicked");
    onNewChat();
    if (!isDesktop) onToggle();
  };

  const handleRenameClick = (chat, e) => {
    e.stopPropagation();
    setRenamingChatId(chat._id);
    setNewTitle(chat.title || "");
    setOpenMenuId(null);
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

  const handleToggleMenu = (chatId, e) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === chatId ? null : chatId);
  };

  const handleGenerateSummary = async (chat, e) => {
    e.stopPropagation();
    setSummarySessionId(chat._id);
    setOpenMenuId(null);

    setSummaryModalOpen(true);

    try {
      await generateSummary(chat._id);
    } catch (error) {
      console.error("Summary generation failed:", error);
    }
  };

  const handleDownloadSummaryPdf = async () => {
    if (summarySessionId && summary) {
      const chat = chatSessions.find((c) => c._id === summarySessionId);
      try {
        await downloadSummaryPdf(summarySessionId, chat?.title || "Chat");
      } catch (error) {
        console.error("PDF download failed:", error);
      }
    }
  };

  // NEW: Handle chat PDF export using the hook
  const handleExportPdfClick = async (chat, e) => {
    e.stopPropagation();
    setOpenMenuId(null);

    try {
      await downloadPdf(chat._id, chat.title || "Chat");
    } catch (error) {
      console.error("PDF export failed:", error);
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
              ? "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md hover:from-emerald-600 hover:to-emerald-700"
              : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-md"
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
                borderTopColor: "#10B981",
                borderLeftColor: darkMode ? "#10B981" : undefined,
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
                    ? "bg-gradient-to-r from-emerald-500/12 to-emerald-600/8 border-emerald-500 shadow-[0_8px_24px_rgba(16,185,129,0.06)]"
                    : "bg-emerald-100 border-emerald-500 shadow-md"
                  : darkMode
                  ? "bg-dark-surface/40 border-transparent hover:bg-dark-elev/60 hover:border-dark-border"
                  : "bg-white/30 border-transparent hover:bg-white/50 hover:border-white/30"
              }`}
            >
              {selectedChatId === chat._id && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full bg-gradient-to-b from-emerald-500 to-emerald-600" />
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
                  className={`w-full px-2 py-1 text-sm rounded focus:outline-none focus:ring-2 focus:ring-emerald-500/30 border ${
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
                            : "text-emerald-900"
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

                  <div className="relative dropdown-menu">
                    <button
                      onClick={(e) => handleToggleMenu(chat._id, e)}
                      className={`p-1.5 rounded transition-colors ${
                        darkMode
                          ? "text-dark-muted hover:bg-dark-elev/50 hover:text-white"
                          : "text-gray-400 hover:bg-black/5 hover:text-gray-600"
                      } ${
                        openMenuId === chat._id
                          ? darkMode
                            ? "bg-dark-elev/50 text-white"
                            : "bg-black/5 text-gray-600"
                          : ""
                      }`}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                      </svg>
                    </button>

                    {openMenuId === chat._id && (
                      <div
                        className={`absolute right-0 top-full mt-1 w-48 rounded-lg shadow-xl border z-50 ${
                          darkMode
                            ? "bg-dark-elev border-dark-border"
                            : "bg-white border-gray-200"
                        }`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {/* Generate Summary */}
                        <button
                          onClick={(e) => handleGenerateSummary(chat, e)}
                          disabled={isSummaryGenerating}
                          className={`w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors ${
                            darkMode
                              ? "text-slate-100 hover:bg-dark-surface"
                              : "text-gray-700 hover:bg-gray-50"
                          } rounded-t-lg disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                          <span className="text-base">🤖</span>
                          <span>Generate Summary</span>
                        </button>

                        {/* Export PDF */}
                        <button
                          onClick={(e) => handleExportPdfClick(chat, e)}
                          disabled={isPdfExporting}
                          className={`w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                            darkMode
                              ? "text-slate-100 hover:bg-dark-surface"
                              : "text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          {isPdfExporting ? (
                            <div className="w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
                          ) : (
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
                                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                              />
                            </svg>
                          )}
                          <span>
                            {isPdfExporting ? "Exporting..." : "Export PDF"}
                          </span>
                        </button>

                        <div
                          className={`h-px ${
                            darkMode ? "bg-dark-border" : "bg-gray-200"
                          }`}
                        />

                        {/* Rename */}
                        <button
                          onClick={(e) => handleRenameClick(chat, e)}
                          className={`w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors ${
                            darkMode
                              ? "text-slate-100 hover:bg-dark-surface"
                              : "text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          <span className="text-base">✎</span>
                          <span>Rename</span>
                        </button>

                        {/* Delete */}
                        <button
                          onClick={(e) => handleDeleteClick(chat, e)}
                          className={`w-full px-4 py-2.5 text-left text-sm flex items-center gap-2 transition-colors rounded-b-lg ${
                            darkMode
                              ? "text-red-400 hover:bg-red-900/20"
                              : "text-red-600 hover:bg-red-50"
                          }`}
                        >
                          <span className="text-base">🗑</span>
                          <span>Delete</span>
                        </button>
                      </div>
                    )}
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
      <>
        <aside className="w-72 h-full flex-shrink-0 relative z-10">
          <SidebarContent />
        </aside>

        {/* Delete Dialog */}
        {deleteDialogOpen && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]">
            <div
              className={`rounded-2xl p-6 max-w-md w-full mx-4 ${
                darkMode
                  ? "bg-dark-surface border border-dark-border"
                  : "bg-white"
              }`}
            >
              <h3
                className={`text-lg font-semibold mb-2 ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}
              >
                Delete Conversation?
              </h3>
              <p
                className={`text-sm mb-6 ${
                  darkMode ? "text-dark-muted" : "text-gray-600"
                }`}
              >
                This will permanently delete "
                {chatToDelete?.title || "this conversation"}" and all its
                messages. This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={cancelDelete}
                  className={`flex-1 px-4 py-2.5 rounded-xl font-medium transition-colors ${
                    darkMode
                      ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="flex-1 px-4 py-2.5 rounded-xl font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Summary Modal */}
        <SummaryModal
          isOpen={summaryModalOpen}
          onClose={() => {
            setSummaryModalOpen(false);
            setSummarySessionId(null);
          }}
          summary={summary}
          isGenerating={isSummaryGenerating}
          error={summaryError}
          onDownloadPdf={handleDownloadSummaryPdf}
          isDownloading={isPdfLoading}
          darkMode={darkMode}
        />
      </>
    );
  }

  /* Mobile Overlay */
  return (
    <>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
            onClick={onToggle}
          />
          <aside className="fixed left-0 top-0 bottom-0 w-80 z-50 lg:hidden">
            <SidebarContent />
          </aside>
        </>
      )}

      {/* Mobile Delete Dialog */}
      {deleteDialogOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div
            className={`rounded-2xl p-6 max-w-md w-full mx-4 ${
              darkMode
                ? "bg-dark-surface border border-dark-border"
                : "bg-white"
            }`}
          >
            <h3
              className={`text-lg font-semibold mb-2 ${
                darkMode ? "text-white" : "text-gray-900"
              }`}
            >
              Delete Conversation?
            </h3>
            <p
              className={`text-sm mb-6 ${
                darkMode ? "text-dark-muted" : "text-gray-600"
              }`}
            >
              This will permanently delete "
              {chatToDelete?.title || "this conversation"}" and all its
              messages.
            </p>
            <div className="flex gap-3">
              <button
                onClick={cancelDelete}
                className={`flex-1 px-4 py-2.5 rounded-xl font-medium transition-colors ${
                  darkMode
                    ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                    : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                }`}
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 px-4 py-2.5 rounded-xl font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Summary Modal */}
      <SummaryModal
        isOpen={summaryModalOpen}
        onClose={() => {
          setSummaryModalOpen(false);
          setSummarySessionId(null);
        }}
        summary={summary}
        isGenerating={isSummaryGenerating}
        error={summaryError}
        onDownloadPdf={handleDownloadSummaryPdf}
        isDownloading={isPdfLoading}
        darkMode={darkMode}
      />
    </>
  );
}

export default ChatHistorySidebar;
