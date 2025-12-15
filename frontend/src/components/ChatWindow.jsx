import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import { sendChatMessage } from "../api";
import { useAuth } from "../context/AuthContext";

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
}) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(currentSessionId);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { isAuthenticated } = useAuth();

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
        "Hey there! I'm your Local Guide. I know every hidden path in this spiritual hub. Where should we start?",
      spiritual_teacher:
        "Namaste. As we walk this sacred land together, what questions burden your heart?",
      trek_companion:
        "Ready for the mountains? The peaks are calling! Let's check the trails and weather.",
      cultural_expert:
        "Welcome. Every stone here whispers an ancient legend. Which story shall I unveil for you today?",
    };

    setMessages([
      {
        id: Date.now(),
        text: welcomeMessages[selectedPersona] || welcomeMessages.local_guide,
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
          text: "I'm having trouble connecting to the spiritual realm right now. Please try again.",
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

  return (
    /* Main Container - The "Glass Sheet" */
    <div className="flex flex-col h-full bg-white/40 backdrop-blur-2xl rounded-3xl border border-white/40 shadow-2xl overflow-hidden relative">
      {/* Decorative Gradient Blob (Optional Background enhancement) */}
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-white/40 to-transparent pointer-events-none z-10" />

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-2 z-0">
        <div className="pt-4 pb-2">
          {/* Space for content to not start abruptly at top */}
        </div>

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onSuggestionClick={(s) => {
              setInputMessage(s);
              inputRef.current?.focus();
            }}
          />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 p-4 text-gray-500 text-sm animate-pulse">
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "0s" }}
            />
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            />
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            />
            <span className="ml-2 font-medium">Consulting the guide...</span>
          </div>
        )}
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input Area - Floating Capsule */}
      <div className="p-5 z-20">
        <form
          onSubmit={handleSendMessage}
          className="relative flex items-center gap-2 max-w-4xl mx-auto"
        >
          {/* Mobile Persona Switcher */}
          <div className="lg:hidden relative">
            <button
              type="button"
              onClick={() => onPersonaSelectorToggle?.(!personaSelectorOpen)}
              className="w-12 h-12 rounded-full bg-white/80 backdrop-blur-xl border border-white/50 text-xl shadow-sm flex items-center justify-center transition-transform active:scale-95"
            >
              {getPersonaIcon(selectedPersona)}
            </button>

            {/* Mobile Persona Popover */}
            {personaSelectorOpen && (
              <div className="absolute bottom-full left-0 mb-4 w-72 bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/50 p-2 z-50 animate-enter origin-bottom-left">
                {personas.map((persona) => (
                  <button
                    key={persona.id}
                    type="button"
                    onClick={() => {
                      onPersonaChange?.(persona.id);
                      onPersonaSelectorToggle?.(false);
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all text-left ${
                      selectedPersona === persona.id
                        ? "bg-indigo-50 text-indigo-900"
                        : "hover:bg-gray-50 text-gray-700"
                    }`}
                  >
                    <span className="text-xl">{persona.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm">
                        {persona.name}
                      </div>
                    </div>
                    {selectedPersona === persona.id && (
                      <span className="text-indigo-600">✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input Field Capsule */}
          <div className="flex-1 relative group">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about temples, treks, or legends..."
              className="w-full pl-5 pr-14 py-4 bg-white/70 hover:bg-white/90 focus:bg-white/95 backdrop-blur-xl border border-white/50 rounded-full shadow-lg shadow-indigo-500/5 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-gray-800 placeholder-gray-500 transition-all duration-300"
              disabled={isLoading}
            />

            {/* Send Button (Inside Capsule) */}
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="absolute right-2 top-2 bottom-2 w-10 h-10 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:bg-gray-400 shadow-md transform active:scale-90"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ChatWindow;
