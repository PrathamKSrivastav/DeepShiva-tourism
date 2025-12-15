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
        if (onNewChatCreated) onNewChatCreated(); // Refresh sidebar
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

  return (
    <div
      className={`flex flex-col h-full ${
        darkMode
          ? "bg-gray-800 backdrop-blur-3xl rounded-3xl border border-gray-700 shadow-2xl"
          : "bg-white/40 backdrop-blur-3xl rounded-3xl border border-white/40 shadow-2xl"
      } overflow-hidden relative z-10`}
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-gradient-to-b from-white/30 to-transparent blur-3xl pointer-events-none z-0" />

      {/* Chat Messages Area */}
      <div
        className={`flex-1 overflow-y-auto no-scrollbar p-4 md:p-8 space-y-4 z-10 ${
          darkMode ? "text-white" : "text-gray-900"
        }`}
      >
        <div className="pt-2"></div>

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onSuggestionClick={(s) => {
              setInputMessage(s);
              inputRef.current?.focus();
            }}
            darkMode={darkMode}
          />
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 p-4 text-indigo-900/50 text-sm animate-pulse">
            <div
              className="w-2 h-2 bg-fuchsia-500 rounded-full animate-bounce"
              style={{ animationDelay: "0s" }}
            />
            <div
              className="w-2 h-2 bg-fuchsia-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.15s" }}
            />
            <div
              className="w-2 h-2 bg-fuchsia-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.3s" }}
            />
            <span className="ml-2 font-medium tracking-wide">
              Consulting the universe...
            </span>
          </div>
        )}
        <div ref={messagesEndRef} className="h-2" />
      </div>

      {/* Input Area */}
      <div
        className={`p-4 md:p-6 z-20 ${
          darkMode
            ? "bg-gray-800/50 border-gray-700"
            : "bg-white/40 border-gray-200"
        } border-t`}
      >
        <form
          onSubmit={handleSendMessage}
          className="relative flex items-center gap-3 max-w-4xl mx-auto"
        >
          {/* Mobile Persona Switcher Button */}
          <div className="lg:hidden relative">
            <button
              type="button"
              onClick={() => onPersonaSelectorToggle?.(!personaSelectorOpen)}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-transform active:scale-95 text-xl shadow-lg ${
                darkMode
                  ? "bg-gray-700/70 backdrop-blur-xl border border-gray-600 shadow-indigo-500/10 text-white"
                  : "bg-white/70 backdrop-blur-xl border border-white/60 shadow-indigo-500/10"
              }`}
            >
              {getPersonaIcon(selectedPersona)}
            </button>

            {/* Mobile Persona Popover */}
            {personaSelectorOpen && (
              <div
                className={`absolute bottom-full left-0 mb-4 w-72 rounded-2xl shadow-2xl border p-2 z-50 animate-enter origin-bottom-left ${
                  darkMode
                    ? "bg-gray-700/80 backdrop-blur-2xl border-gray-600"
                    : "bg-white/80 backdrop-blur-2xl border-white/50"
                }`}
              >
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
                        ? darkMode
                          ? "bg-indigo-900/50 text-white"
                          : "bg-fuchsia-50 text-fuchsia-900"
                        : darkMode
                        ? "hover:bg-gray-600 text-gray-200"
                        : "hover:bg-white/50 text-gray-700"
                    }`}
                  >
                    <span className="text-xl">{persona.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-sm">
                        {persona.name}
                      </div>
                    </div>
                    {selectedPersona === persona.id && (
                      <span
                        className={
                          darkMode ? "text-indigo-400" : "text-fuchsia-600"
                        }
                      >
                        ✓
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about temples, treks, or legends..."
            className={`flex-1 pl-6 pr-14 py-4 rounded-full shadow-xl shadow-indigo-900/5 focus:outline-none focus:ring-2 transition-all duration-300 ${
              darkMode
                ? "bg-gray-700/60 backdrop-blur-xl border border-gray-600 hover:bg-gray-700/80 focus:bg-gray-700/90 focus:ring-indigo-500/30 text-white placeholder-gray-400"
                : "bg-white/60 hover:bg-white/80 focus:bg-white/90 backdrop-blur-xl border border-white/50 focus:ring-fuchsia-400/30 text-gray-800 placeholder-gray-500"
            }`}
            disabled={isLoading}
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="absolute right-2 top-2 bottom-2 w-10 h-10 bg-gradient-to-r from-red-600 to-fuchsia-600 hover:from-red-500 hover:to-fuchsia-500 text-white rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:grayscale shadow-md transform active:scale-90 hover:shadow-lg"
          >
            <svg
              width="18"
              height="18"
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
        </form>
      </div>
    </div>
  );
}

export default ChatWindow;