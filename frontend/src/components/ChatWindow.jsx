import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import { sendChatMessage } from "../api";
import { useAuth } from "../context/AuthContext";
import PdfExportButton from "./PdfExportButton"; // ← ADDED

import { useSummaryGenerator } from "../hooks/useSummaryGenerator";
import SummaryModal from "./SummaryModal";
import SummaryButton from "./SummaryButton";

function ChatWindow({
  selectedPersona,
  personaInfo,
  selectedChat,
  newChatTrigger,
  currentSessionId,
  onSessionCreated,
  personas = [],
  onPersonaChange,
  personaSelectorOpen,
  onPersonaSelectorToggle,
  onNewChatCreated,
  darkMode,
}) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(currentSessionId);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { isAuthenticated } = useAuth();


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

  useEffect(() => setSessionId(currentSessionId), [currentSessionId]);

  useEffect(() => {
    if (selectedChat) loadSelectedChat(selectedChat);
    else showWelcomeMessage();
  }, [selectedChat, selectedPersona, newChatTrigger]);

  useEffect(() => scrollToBottom(), [messages]);

  const loadSelectedChat = (chat) => {
    setSessionId(chat._id);
    const formattedMessages = chat.messages.map((msg, idx) => ({
      id: `history-${idx}`,
      text: msg.content,
      sender: msg.role === "user" ? "user" : "bot",
      persona: msg.persona || selectedPersona,
      intent: msg.intent,
      timestamp: new Date(msg.timestamp),
    }));
    setMessages(formattedMessages);
  };

  const showWelcomeMessage = () => {
    setSessionId(null);
    const welcomeMessages = {
      local_guide:
        "Hey there! I'm your Local Guide. I've been exploring India for years. Planning a Char Dham trip, or looking for some adventure?",
      spiritual_teacher:
        "Namaste. I am honored to guide you through the spiritual essence of this holy land. What burdens your heart today?",
      trek_companion:
        "Hey adventure buddy! Ready to explore the mountains? Let's check the trails and weather for Kedarnath or Valley of Flowers!",
      cultural_expert:
        "Namaste! Every stone here whispers an ancient legend. Which myth or tradition shall I unveil for you today?",
    };

    setMessages([
      {
        id: Date.now(),
        text:
          welcomeMessages[selectedPersona] || welcomeMessages.local_guide,
        sender: "bot",
        persona: selectedPersona,
        timestamp: new Date(),
      },
    ]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await sendChatMessage(
        inputMessage,
        selectedPersona,
        {},
        sessionId
      );

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
        if (onSessionCreated) onSessionCreated(response.session_id);
        if (onNewChatCreated) onNewChatCreated();
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: response.response,
          sender: "bot",
          persona: response.persona,
          intent: response.intent,
          suggestions: response.suggestions,
          timestamp: new Date(),
          chatSaved: response.chat_saved,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: "I apologize, but I'm having trouble connecting right now. Please try again.",
          sender: "bot",
          persona: selectedPersona,
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const getPersonaIcon = (id) =>
    personas.find((p) => p.id === id)?.icon || "🎭";

  const handleGenerateSummary = async () => {
  if (!sessionId) {
    alert('No active session to summarize. Start chatting first!');
    return;
  }

  if (messages.length < 2) {
    alert('Need at least 2 messages to generate a summary');
    return;
  }

  try {
    setShowSummaryModal(true);
    await generateSummary(sessionId);
  } catch (error) {
    console.error('Failed to generate summary:', error);
  }
};

const handleDownloadSummary = async () => {
  if (!sessionId) return;

  try {
    await downloadSummaryPdf(
      sessionId,
      selectedChat?.title || 'chat'
    );
  } catch (error) {
    console.error('Failed to download summary PDF:', error);
  }
};

const handleCloseSummaryModal = () => {
  setShowSummaryModal(false);
  clearSummary();
};

  return (
    <div
      className={`flex flex-col h-screen transition-colors ${
        darkMode ? "bg-gray-900" : "bg-gray-50"
      }`}
    >
      {/* ========== HEADER WITH PDF BUTTON ========== */}
      <div
        className={`border-b shadow-sm px-4 py-3 ${
          darkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-gray-200"
        }`}
      >
        <div className="flex items-center justify-between">
          {/* Left Side: Session Title */}
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getPersonaIcon(selectedPersona)}</span>
            <div>
              <h2
                className={`text-lg font-semibold ${
                  darkMode ? "text-white" : "text-gray-800"
                }`}
              >
                {selectedChat?.title || "New Conversation"}
              </h2>
              <p
                className={`text-sm ${
                  darkMode ? "text-gray-400" : "text-gray-500"
                }`}
              >
                {messages.length} messages • {selectedPersona.replace("_", " ")}
              </p>
            </div>
          </div>

          {/* ✨ RIGHT SIDE: ACTION BUTTONS ✨ */}
<div className="flex items-center gap-2">
  {/* PDF Export Button */}
  {sessionId && selectedChat && (
    <PdfExportButton
      sessionId={sessionId}
      sessionTitle={selectedChat?.title || "Chat"}
      variant="secondary"
      darkMode={darkMode}
    />
  )}
  
  {/* ✨ NEW: AI Summary Button ✨ */}
  {sessionId && messages.length >= 2 && (
    <SummaryButton
      onClick={handleGenerateSummary}
      isGenerating={isGeneratingSummary}
      disabled={!sessionId || messages.length < 2}
      variant="primary"
    />
  )}
</div>

        </div>
      </div>

      {/* ========== MESSAGES AREA ========== */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isUser={msg.sender === "user"}
              darkMode={darkMode}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div
                className={`px-4 py-3 rounded-lg ${
                  darkMode ? "bg-gray-800" : "bg-gray-100"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-teal-500 rounded-full animate-bounce delay-100" />
                    <span className="w-2 h-2 bg-teal-500 rounded-full animate-bounce delay-200" />
                  </div>
                  <span
                    className={`text-sm ${
                      darkMode ? "text-gray-400" : "text-gray-500"
                    }`}
                  >
                    Thinking...
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ========== INPUT AREA ========== */}
      <div
        className={`border-t px-4 py-4 ${
          darkMode
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-gray-200"
        }`}
      >
        <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Message ${selectedPersona.replace("_", " ")}...`}
              disabled={isLoading}
              className={`flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors ${
                darkMode
                  ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400"
                  : "bg-white border-gray-300 text-gray-900 placeholder-gray-500"
              } disabled:opacity-50`}
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
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
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
              Send
            </button>
          </div>
        </form>
      </div>
       
       
       {/* ✨ ADD THIS MODAL HERE (before closing div) ✨ */}
      <SummaryModal
        isOpen={showSummaryModal}
        onClose={handleCloseSummaryModal}
        summary={summary}
        isGenerating={isGeneratingSummary}
        error={summaryError}
        onDownloadPdf={handleDownloadSummary}
        isDownloading={isDownloadingSummary}
      />


    </div>
  );
}

export default ChatWindow;
