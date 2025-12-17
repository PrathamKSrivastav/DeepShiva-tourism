import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import { sendChatMessage, sendAudioMessage } from "../api";
import { useAuth } from "../context/AuthContext";

function ChatWindow({
  selectedPersona,
  selectedChat,
  newChatTrigger,
  currentSessionId,
  onSessionCreated,
  personas = [],
  onPersonaChange,
  onNewChatCreated,
  darkMode,
  chatSessions = [],
}) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(currentSessionId);
  const [lastPersona, setLastPersona] = useState(selectedPersona);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [personaSelectorOpen, setPersonaSelectorOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const personaMenuRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => setSessionId(currentSessionId), [currentSessionId]);

  // Cleanup recording timer on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, []);

  // Close persona selector when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        personaSelectorOpen &&
        personaMenuRef.current &&
        !personaMenuRef.current.contains(e.target)
      ) {
        setPersonaSelectorOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [personaSelectorOpen]);

  useEffect(() => {
    if (!hasInitialized) {
      console.log(
        "🎉 Initial mount - showing welcome message for:",
        selectedPersona
      );
      showWelcomeMessage();
      setHasInitialized(true);
    }
  }, [hasInitialized, selectedPersona]);

  useEffect(() => {
    if (!hasInitialized) return;

    if (lastPersona !== selectedPersona) {
      console.log(
        `🔄 Persona switched from ${lastPersona} to ${selectedPersona}`
      );
      setLastPersona(selectedPersona);

      if (selectedChat) {
        loadSelectedChat(selectedChat);
      } else {
        showWelcomeMessage();
      }
      return;
    }

    if (selectedChat) {
      loadSelectedChat(selectedChat);
      return;
    }

    if (newChatTrigger) {
      showWelcomeMessage();
    }
  }, [selectedChat, selectedPersona, newChatTrigger, hasInitialized]);

  useEffect(() => scrollToBottom(), [messages]);

  useEffect(() => {
    const handleChatDeleted = (event) => {
      const deletedChatId = event.detail?.chatId;
      if (deletedChatId && deletedChatId === sessionId) {
        showWelcomeMessage();
        setSessionId(null);
      }
    };

    window.addEventListener("chat-deleted", handleChatDeleted);
    return () => window.removeEventListener("chat-deleted", handleChatDeleted);
  }, [sessionId, selectedPersona]);

  useEffect(() => {
    const handleLogout = () => {
      showWelcomeMessage();
      setSessionId(null);
      setIsLoading(false);
    };

    window.addEventListener("user-logout", handleLogout);
    return () => window.removeEventListener("user-logout", handleLogout);
  }, [selectedPersona]);

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
    setInputMessage("");
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

  const startRecording = async () => {
    try {
      console.log("🎤 Starting audio recording...");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        console.log("🛑 Recording stopped");
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Send audio to backend
        await handleAudioSubmit(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error("❌ Microphone access denied:", error);
      alert("Please allow microphone access to use audio recording.");
    }
  };

  const stopRecording = () => {
    console.log("⏹️ Stopping recording...");
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      setRecordingTime(0);
    }
  };

  const handleAudioSubmit = async (audioBlob) => {
    setIsLoading(true);
    try {
      console.log("📤 Sending audio to backend...");
      const response = await sendAudioMessage(
        audioBlob,
        selectedPersona,
        sessionId
      );

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
        if (onSessionCreated) onSessionCreated(response.session_id);
        if (onNewChatCreated) onNewChatCreated();
      }

      // Add transcription as user message
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: response.transcription,
          sender: "user",
          timestamp: new Date(),
          isAudio: true,
        },
      ]);

      // Add response
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: response.response,
          sender: "bot",
          persona: response.persona,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error("❌ Audio submission failed:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: "Sorry, I couldn't process your audio. Please try again.",
          sender: "bot",
          persona: selectedPersona,
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePersonaSelect = (personaId) => {
    if (personaId === selectedPersona) {
      setPersonaSelectorOpen(false);
      return;
    }

    // Find most recent chat for this persona
    const personaChats = chatSessions.filter(
      (chat) => chat.persona === personaId
    );

    if (personaChats.length > 0) {
      const mostRecentChat = personaChats.sort(
        (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
      )[0];
      onPersonaChange(personaId, mostRecentChat);
    } else {
      onPersonaChange(personaId, null);
    }

    setPersonaSelectorOpen(false);
  };

  const currentPersona = personas.find((p) => p.id === selectedPersona);

  return (
    <div
      className={`flex flex-col h-full ${
        darkMode
          ? "bg-dark-surface rounded-3xl border border-dark-border shadow-xl"
          : "bg-white/40 rounded-3xl border border-white/40 shadow-2xl"
      } overflow-hidden relative z-10`}
    >
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
            <span
              className={`ml-3 text-sm ${
                darkMode ? "text-dark-muted" : "text-gray-500"
              }`}
            >
              Consulting the universe...
            </span>
          </div>
        )}
        <div ref={messagesEndRef} className="h-2" />
      </div>

      {/* Input Area - FIXED FOR MOBILE */}
      <div
        className={`p-3 sm:p-4 md:p-6 z-20 ${
          darkMode
            ? "bg-dark-elev/80 border-t border-dark-border"
            : "bg-white/50 border-t border-white/20"
        }`}
      >
        {/* Persona Selector - Mobile: Full width button */}
        <div className="mb-2 sm:mb-3 md:hidden">
          <div className="relative" ref={personaMenuRef}>
            <button
              type="button"
              onClick={() => setPersonaSelectorOpen(!personaSelectorOpen)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl transition-colors ${
                darkMode
                  ? "bg-dark-elev border border-dark-border text-slate-100 hover:bg-dark-elev/80"
                  : "bg-white/80 border border-white/60 text-gray-700 hover:bg-white"
              }`}
              title="Select persona"
            >
              <span className="text-sm font-medium truncate">
                {currentPersona?.name || "Select Persona"}
              </span>
              <svg
                className={`w-4 h-4 flex-shrink-0 transition-transform ${
                  personaSelectorOpen ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {/* Persona Dropdown */}
            {personaSelectorOpen && (
              <div
                className={`absolute bottom-full left-0 right-0 mb-2 max-h-96 overflow-y-auto rounded-2xl shadow-2xl border ${
                  darkMode
                    ? "bg-dark-surface border-dark-border"
                    : "bg-white border-gray-200"
                } z-50`}
              >
                <div
                  className={`p-3 border-b ${
                    darkMode ? "border-dark-border" : "border-gray-200"
                  }`}
                >
                  <h3
                    className={`text-sm font-semibold ${
                      darkMode ? "text-slate-100" : "text-gray-800"
                    }`}
                  >
                    Choose Your Guide
                  </h3>
                </div>

                <div className="p-2 space-y-1">
                  {personas.map((persona) => {
                    const isSelected = selectedPersona === persona.id;
                    const personaChatCount = chatSessions.filter(
                      (chat) => chat.persona === persona.id
                    ).length;

                    return (
                      <button
                        key={persona.id}
                        onClick={() => handlePersonaSelect(persona.id)}
                        className={`w-full text-left p-3 rounded-xl transition-all ${
                          isSelected
                            ? darkMode
                              ? "bg-dark-elev ring-1 ring-accent-indigo/30"
                              : "bg-indigo-50 ring-1 ring-indigo-200"
                            : darkMode
                            ? "hover:bg-dark-elev/50"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`flex-shrink-0 text-2xl p-2 rounded-lg ${
                              isSelected
                                ? "bg-gradient-to-tr from-accent-indigo/20 to-accent-fuchsia/10"
                                : ""
                            }`}
                          >
                            {persona.icon}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <span
                                className={`font-semibold text-sm ${
                                  isSelected
                                    ? darkMode
                                      ? "text-white"
                                      : "text-indigo-900"
                                    : darkMode
                                    ? "text-slate-100"
                                    : "text-gray-800"
                                }`}
                              >
                                {persona.name}
                              </span>
                              {personaChatCount > 0 && (
                                <span
                                  className={`text-xs px-2 py-0.5 rounded-full ${
                                    isSelected
                                      ? darkMode
                                        ? "bg-accent-indigo/20 text-accent-indigo"
                                        : "bg-indigo-100 text-indigo-700"
                                      : darkMode
                                      ? "bg-dark-elev text-dark-muted"
                                      : "bg-gray-200 text-gray-600"
                                  }`}
                                >
                                  {personaChatCount}
                                </span>
                              )}
                            </div>
                            <p
                              className={`text-xs line-clamp-2 ${
                                darkMode ? "text-dark-muted" : "text-gray-500"
                              }`}
                            >
                              {persona.description}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Form */}
        <form
          onSubmit={handleSendMessage}
          className="flex items-center gap-2 max-w-4xl mx-auto"
        >
          {/* Desktop Persona Selector */}
          <div className="hidden md:block relative" ref={personaMenuRef}>
            <button
              type="button"
              onClick={() => setPersonaSelectorOpen(!personaSelectorOpen)}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl transition-colors ${
                darkMode
                  ? "bg-dark-elev border border-dark-border text-slate-100 hover:bg-dark-elev/80"
                  : "bg-white/80 border border-white/60 text-gray-700 hover:bg-white"
              }`}
              title="Select persona"
            >
              <span className="text-sm font-medium">
                {currentPersona?.name || "Select Persona"}
              </span>
              <svg
                className={`w-4 h-4 transition-transform ${
                  personaSelectorOpen ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {/* Desktop Persona Dropdown */}
            {personaSelectorOpen && (
              <div
                className={`absolute bottom-full left-0 mb-2 w-80 max-h-96 overflow-y-auto rounded-2xl shadow-2xl border ${
                  darkMode
                    ? "bg-dark-surface border-dark-border"
                    : "bg-white border-gray-200"
                } z-50`}
              >
                <div
                  className={`p-3 border-b ${
                    darkMode ? "border-dark-border" : "border-gray-200"
                  }`}
                >
                  <h3
                    className={`text-sm font-semibold ${
                      darkMode ? "text-slate-100" : "text-gray-800"
                    }`}
                  >
                    Choose Your Guide
                  </h3>
                </div>

                <div className="p-2 space-y-1">
                  {personas.map((persona) => {
                    const isSelected = selectedPersona === persona.id;
                    const personaChatCount = chatSessions.filter(
                      (chat) => chat.persona === persona.id
                    ).length;

                    return (
                      <button
                        key={persona.id}
                        onClick={() => handlePersonaSelect(persona.id)}
                        className={`w-full text-left p-3 rounded-xl transition-all ${
                          isSelected
                            ? darkMode
                              ? "bg-dark-elev ring-1 ring-accent-indigo/30"
                              : "bg-indigo-50 ring-1 ring-indigo-200"
                            : darkMode
                            ? "hover:bg-dark-elev/50"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`flex-shrink-0 text-2xl p-2 rounded-lg ${
                              isSelected
                                ? "bg-gradient-to-tr from-accent-indigo/20 to-accent-fuchsia/10"
                                : ""
                            }`}
                          >
                            {persona.icon}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <span
                                className={`font-semibold text-sm ${
                                  isSelected
                                    ? darkMode
                                      ? "text-white"
                                      : "text-indigo-900"
                                    : darkMode
                                    ? "text-slate-100"
                                    : "text-gray-800"
                                }`}
                              >
                                {persona.name}
                              </span>
                              {personaChatCount > 0 && (
                                <span
                                  className={`text-xs px-2 py-0.5 rounded-full ${
                                    isSelected
                                      ? darkMode
                                        ? "bg-accent-indigo/20 text-accent-indigo"
                                        : "bg-indigo-100 text-indigo-700"
                                      : darkMode
                                      ? "bg-dark-elev text-dark-muted"
                                      : "bg-gray-200 text-gray-600"
                                  }`}
                                >
                                  {personaChatCount}
                                </span>
                              )}
                            </div>
                            <p
                              className={`text-xs line-clamp-2 ${
                                darkMode ? "text-dark-muted" : "text-gray-500"
                              }`}
                            >
                              {persona.description}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Text Input - Fixed padding */}
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about temples, treks..."
              className={`w-full pl-3 sm:pl-4 pr-20 sm:pr-24 py-2.5 sm:py-3 rounded-xl shadow-sm focus:outline-none focus:ring-2 transition-all duration-300 text-sm sm:text-base ${
                darkMode
                  ? "bg-dark-elev border border-dark-border hover:bg-dark-elev/95 focus:bg-dark-elev/95 focus:ring-accent-indigo/30 text-slate-100 placeholder-dark-muted"
                  : "bg-white/60 hover:bg-white/80 focus:bg-white/90 border border-white/40 focus:ring-emerald-400/30 text-gray-800 placeholder-gray-500"
              }`}
              disabled={isLoading || isRecording}
            />

            {/* Mic Button - Inside input, positioned absolutely */}
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              className={`absolute right-10 sm:right-12 top-1/2 -translate-y-1/2 w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center transition-all ${
                isRecording
                  ? "bg-red-500 hover:bg-red-600 animate-pulse"
                  : darkMode
                  ? "hover:bg-dark-border text-slate-100"
                  : "hover:bg-gray-100 text-emerald-600"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={
                isRecording ? `Recording... ${recordingTime}s` : "Record audio"
              }
            >
              {isRecording ? (
                <span className="text-white text-[10px] sm:text-xs font-semibold">
                  {recordingTime}s
                </span>
              ) : (
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path
                    d="M12 1c-1.66 0-3 1.34-3 3v8c0 1.66 1.34 3 3 3s3-1.34 3-3V4c0-1.66-1.34-3-3-3z"
                    fill="currentColor"
                  />
                  <path d="M19 10v2c0 3.87-3.13 7-7 7s-7-3.13-7-7v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              )}
            </button>

            {/* Send Button - Inside input, positioned absolutely */}
            <button
              type="submit"
              disabled={isLoading || !inputMessage.trim() || isRecording}
              className={`absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                darkMode
                  ? ""
                  : "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700"
              }`}
              style={
                darkMode
                  ? {
                      background:
                        "linear-gradient(90deg, #10B981 0%, #059669 55%)",
                      boxShadow:
                        "0 4px 12px rgba(16,185,129,0.12), 0 2px 6px rgba(5,150,105,0.06)",
                    }
                  : { boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)" }
              }
            >
              <svg
                width="14"
                height="14"
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
          </div>
        </form>
      </div>
    </div>
  );
}

export default ChatWindow;
