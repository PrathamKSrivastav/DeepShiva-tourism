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
      ? "bg-dark-surface rounded-3xl border border-dark-border shadow-xl"
      : "bg-white/40 rounded-3xl border border-white/40 shadow-2xl"
  } overflow-hidden relative z-10`}
>
  

      {/* Decorative Atmospheric Light */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-gradient-to-b from-white/30 to-transparent blur-3xl pointer-events-none z-0" />

      {/* Chat Messages Area */}
      <div
        className={`flex-1 overflow-y-auto no-scrollbar p-4 md:p-6 space-y-4 z-10 ${
          darkMode ? "text-slate-100" : "text-gray-900"
        }`}
      >
        <div className="pt-2" />

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
          <div className="flex items-center gap-3 p-4 text-sm">
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-accent-fuchsia/90 animate-pulse inline-block" />
              <span className="w-2 h-2 rounded-full bg-accent-indigo/90 animate-pulse inline-block ml-1" />
              <span className="w-2 h-2 rounded-full bg-accent-rose/85 animate-pulse inline-block ml-1" />
            </div>
            <span className="ml-3 text-dark-muted text-sm">
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
            ? "bg-dark-elev/80 border-t border-dark-border"
            : "bg-white/50 border-t border-white/20"
        }`}
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
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-transform active:scale-95 text-xl shadow-md ${
                darkMode
                  ? "bg-dark-elev border border-dark-border text-slate-100"
                  : "bg-white/80 border border-white/60"
              }`}
            >
              {getPersonaIcon(selectedPersona)}
            </button>
          </div>

          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about temples, treks, or legends..."
            className={`flex-1 pl-6 pr-14 py-4 rounded-full shadow-sm focus:outline-none focus:ring-2 transition-all duration-300 ${
              darkMode
                ? "bg-dark-elev border border-dark-border hover:bg-dark-elev/95 focus:bg-dark-elev/95 focus:ring-accent-indigo/30 text-slate-100 placeholder-dark-muted"
                : "bg-white/60 hover:bg-white/80 focus:bg-white/90 border border-white/40 focus:ring-fuchsia-400/30 text-gray-800 placeholder-gray-500"
            }`}
            disabled={isLoading}
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="absolute right-2 top-2 bottom-2 w-10 h-10 rounded-full flex items-center justify-center transition-transform disabled:opacity-50"
            style={{
              background: darkMode
                ? "linear-gradient(90deg, rgba(99,102,241,1) 0%, rgba(217,70,239,1) 55%)"
                : undefined,
              boxShadow: darkMode
                ? "0 6px 20px rgba(99,102,241,0.12), 0 2px 8px rgba(217,70,239,0.06)"
                : undefined,
            }}
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
              className="text-white"
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
