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
}) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(currentSessionId);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { isAuthenticated } = useAuth();

  // Update session ID when prop changes
  useEffect(() => {
    setSessionId(currentSessionId);
  }, [currentSessionId]);

  // Load selected chat or welcome message
  useEffect(() => {
    if (selectedChat) {
      loadSelectedChat(selectedChat);
    } else {
      showWelcomeMessage();
    }
  }, [selectedChat, selectedPersona, newChatTrigger]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSelectedChat = (chat) => {
    console.log("📖 Loading chat session:", chat._id);
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
    console.log("👋 Showing welcome message for:", selectedPersona);
    setSessionId(null);

    const welcomeMessages = {
      local_guide:
        "Hey there! I'm your Local Guide. I've been exploring India for years and know all the insider tips. What brings you to this Spiritual Hub? Planning a Char Dham trip, or looking for some adventure?",
      spiritual_teacher:
        " Namaste, blessed soul. I am honored to guide you through the spiritual essence to this incredibly large Spiritual Hub. Each temple, each river, each peak here resonates with divine energy. What aspect of this holy land calls to your heart?",
      trek_companion:
        " Hey adventure buddy! Ready to explore the mountains? I'm here to help you plan treks, check weather, and keep you safe. Whether it's Valley of Flowers or Kedarnath trek - let's gear up! What's your adventure goal?",
      cultural_expert:
        " Namaste and welcome! As a Cultural Expert, I'll unveil the rich tapestry of myths, legends, and traditions woven into India's landscape. Every stone here has a story spanning millennia. What cultural aspect would you like to explore?",
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

    console.log("📤 Sending message with session:", sessionId);

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
      // Send message with session ID
      const response = await sendChatMessage(
        inputMessage,
        selectedPersona,
        {},
        sessionId
      );

      console.log("📥 Response:", response);

      // Update session ID if new session was created
      if (response.session_id && !sessionId) {
        console.log("✅ New session created:", response.session_id);
        setSessionId(response.session_id);
        if (onSessionCreated) {
          onSessionCreated(response.session_id);
        }
      }

      const botMessage = {
        id: Date.now() + 1,
        text: response.response,
        sender: "bot",
        persona: response.persona,
        intent: response.intent,
        suggestions: response.suggestions,
        timestamp: new Date(),
        chatSaved: response.chat_saved,
      };

      setMessages((prev) => [...prev, botMessage]);

      if (response.session_id && !sessionId) {
        console.log("✅ New session created:", response.session_id);
        setSessionId(response.session_id);
        if (onSessionCreated) {
          onSessionCreated(response.session_id); // This triggers the refresh
        }
      }
    } catch (error) {
      console.error("❌ Error sending message:", error);

      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I'm having trouble connecting right now. Please try again in a moment. ",
        sender: "bot",
        persona: selectedPersona,
        timestamp: new Date(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    inputRef.current?.focus();
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-[calc(100vh-16rem)]">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4 text-white">
        <div className="flex items-center space-x-3">
          <div className="text-3xl">{personaInfo?.icon || "🤖"}</div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg">
              {personaInfo?.name || "AI Guide"}
            </h3>
            <p className="text-sm text-indigo-100">
              {personaInfo?.description || "Your guide to India"}
            </p>
          </div>
          {sessionId && (
            <div className="text-xs bg-white/20 px-3 py-1 rounded-full">
              💾 Session Active
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onSuggestionClick={handleSuggestionClick}
          />
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-500">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSendMessage} className="flex space-x-3">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={`Ask ${personaInfo?.name || "your guide"} anything...`}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              !inputMessage.trim() || isLoading
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-indigo-600 text-white hover:bg-indigo-700"
            }`}
            disabled={!inputMessage.trim() || isLoading}
          >
            {isLoading ? "⏳" : "📤"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatWindow;
