import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import LocationMap from "./LocationMap";
import "leaflet/dist/leaflet.css";

function MessageBubble({ message, onSuggestionClick, darkMode }) {
  const isUser = message.sender === "user";
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Extract geo data if present
  const geoDataRegex = /<\|GEO_DATA\|>({[^}]+})<\|GEO_DATA\|>/;
  const geoMatch = message.text.match(geoDataRegex);
  console.log(message.text);
  
  let geoData = null;
  if (geoMatch) {
    try {
      // Parse the geo data string (it's formatted as a dictionary)
      const geoString = geoMatch[1];
      const latMatch = geoString.match(/latitude['":\s]+([0-9.-]+)/);
      const lonMatch = geoString.match(/longitude['":\s]+([0-9.-]+)/);
      const locMatch = geoString.match(/location['":\s]+['"]([^'"]+)['"]/);
      
      if (latMatch && lonMatch) {
        geoData = {
          latitude: parseFloat(latMatch[1]),
          longitude: parseFloat(lonMatch[1]),
          location: locMatch ? locMatch[1] : ''
        };
      }
    } catch (e) {
      console.error("Failed to parse geo data:", e);
    }
  }

  // Clean JSON code blocks and geo data from message text for display
  const cleanText = message.text
    .replace(/```json[\s\S]*?```/g, "")
    .replace(geoDataRegex, "")
    .trim();

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

const handleSpeak = () => {
  // Stop if already speaking
  if (isSpeaking) {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    return;
  }

  // Check if speech synthesis is supported
  if (!("speechSynthesis" in window)) {
    alert("Text-to-speech is not supported in your browser.");
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  // Create speech utterance
  const utterance = new SpeechSynthesisUtterance(cleanText);

  // Configure voice settings - faster and more natural
  utterance.rate = 1.0; // Slightly faster (was 1.0)
  utterance.pitch = 0.7; // Natural pitch
  utterance.volume = 1.0; // Full volume

  // Try to find an Indian English voice
  const voices = window.speechSynthesis.getVoices();

  console.log(voices);

  const indianVoice = voices.find(
    (voice) =>
      voice.lang.includes("hi-IN") || voice.name.toLowerCase().includes("india")
  );

  const naturalVoice = voices.find(
    (voice) =>
      voice.lang.startsWith("en") &&
      (voice.name.includes("Natural") ||
        voice.name.includes("Google") ||
        voice.name.includes("Premium"))
  );

  const fallbackVoice = voices.find((voice) => voice.lang.startsWith("en"));

  // Use best available voice
  if (indianVoice) {
    utterance.voice = indianVoice;
    console.log("🎙️ Using Indian voice:", indianVoice.name);
  } else if (naturalVoice) {
    utterance.voice = naturalVoice;
    console.log("🎙️ Using natural voice:", naturalVoice.name);
  } else if (fallbackVoice) {
    utterance.voice = fallbackVoice;
    console.log("🎙️ Using fallback voice:", fallbackVoice.name);
  }

  // Event handlers
  utterance.onstart = () => setIsSpeaking(true);
  utterance.onend = () => setIsSpeaking(false);
  utterance.onerror = () => setIsSpeaking(false);

  // Speak
  window.speechSynthesis.speak(utterance);
};

  return (
    <div
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      } mb-6 animate-enter`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] flex ${
          isUser ? "flex-row-reverse" : "flex-row"
        } items-start gap-2`}
      >
        {/* Speaker Button */}
        <button
          onClick={handleSpeak}
          className={`flex-shrink-0 mt-1 w-7 h-7 rounded-full flex items-center justify-center transition-all hover:scale-110 ${
            isSpeaking
              ? darkMode
                ? "bg-emerald-500 text-white animate-pulse"
                : "bg-emerald-500 text-white animate-pulse"
              : darkMode
              ? "bg-dark-elev hover:bg-dark-border text-slate-400 hover:text-emerald-400"
              : "bg-white/60 hover:bg-white text-gray-500 hover:text-emerald-600"
          } border ${darkMode ? "border-dark-border" : "border-white/40"}`}
          title={isSpeaking ? "Stop speaking" : "Read aloud"}
        >
          {isSpeaking ? (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
            </svg>
          )}
        </button>

        {/* Message Content */}
        <div
          className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
        >
          {!isUser && message.persona && (
            <span
              className={`text-[10px] uppercase tracking-wider mb-1 ml-2 font-bold ${
                darkMode ? "text-slate-400" : "text-gray-500/80"
              }`}
            >
              {message.persona.replace("_", " ")}
            </span>
          )}

          {/* Message Bubble */}
          <div
            className={`relative px-5 py-3.5 text-[15px] leading-relaxed shadow-sm backdrop-blur-md border 
              ${
                isUser
                  ? "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-xl rounded-br-none border-white/30 shadow-emerald-500/30"
                  : message.isError
                  ? darkMode
                    ? "bg-red-900/40 text-red-200 rounded-2xl rounded-bl-sm border-red-800/50"
                    : "bg-red-50/90 text-red-800 rounded-2xl rounded-bl-sm border-red-200"
                  : darkMode
                  ? "bg-dark-elev/80 hover:bg-dark-elev transition-colors text-slate-100 rounded-2xl rounded-bl-sm border-dark-border shadow-gray-900/20"
                  : "bg-white/60 hover:bg-white/70 transition-colors text-gray-800 rounded-2xl rounded-bl-sm border-white/40 shadow-gray-900/5"
              }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap font-normal">{message.text}</p>
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ node, ...props }) => (
                      <p className="mb-2 last:mb-0" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul
                        className={`list-disc list-outside ml-5 my-2 space-y-1 ${
                          darkMode ? "text-slate-100" : "text-gray-800"
                        }`}
                        {...props}
                      />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol
                        className={`list-decimal list-outside ml-5 my-2 space-y-1 ${
                          darkMode ? "text-slate-100" : "text-gray-800"
                        }`}
                        {...props}
                      />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="leading-relaxed" {...props} />
                    ),
                    strong: ({ node, ...props }) => (
                      <strong
                        className={`font-semibold ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                        {...props}
                      />
                    ),
                    em: ({ node, ...props }) => (
                      <em className="italic" {...props} />
                    ),
                    code: ({ node, inline, ...props }) =>
                      inline ? (
                        <code
                          className={`px-1.5 py-0.5 rounded text-sm font-mono ${
                            darkMode
                              ? "bg-dark-surface text-emerald-300"
                              : "bg-emerald-100 text-emerald-800"
                          }`}
                          {...props}
                        />
                      ) : (
                        <code
                          className={`block px-3 py-2 rounded-lg text-sm font-mono overflow-x-auto ${
                            darkMode
                              ? "bg-dark-surface text-slate-200"
                              : "bg-gray-100 text-gray-800"
                          }`}
                          {...props}
                        />
                      ),
                    pre: ({ node, ...props }) => (
                      <pre
                        className={`rounded-lg overflow-hidden my-2 ${
                          darkMode ? "bg-dark-surface" : "bg-gray-100"
                        }`}
                        {...props}
                      />
                    ),
                    a: ({ node, ...props }) => (
                      <a
                        className={`underline ${
                          darkMode
                            ? "text-emerald-300 hover:text-emerald-200"
                            : "text-emerald-600 hover:text-emerald-800"
                        }`}
                        target="_blank"
                        rel="noopener noreferrer"
                        {...props}
                      />
                    ),
                    h1: ({ node, ...props }) => (
                      <h1
                        className={`text-xl font-bold mb-2 ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                        {...props}
                      />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2
                        className={`text-lg font-bold mb-2 ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                        {...props}
                      />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3
                        className={`text-base font-semibold mb-1 ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                        {...props}
                      />
                    ),
                    blockquote: ({ node, ...props }) => (
                      <blockquote
                        className={`border-l-4 pl-4 my-2 italic ${
                          darkMode
                            ? "border-emerald-500 text-slate-300"
                            : "border-emerald-400 text-gray-700"
                        }`}
                        {...props}
                      />
                    ),
                  }}
                >
                  {cleanText}
                </ReactMarkdown>
              </div>
            )}
          </div>
          {/* Map Display */}
          {!isUser && geoData && geoData.latitude && geoData.longitude && (
            <div
              className={`mt-3 rounded-xl overflow-hidden border shadow-md ${
                darkMode
                  ? "border-dark-border shadow-gray-900/50"
                  : "border-gray-200 shadow-gray-300/50"
              }`}
              style={{ width: "100%", maxWidth: "500px" }}
            >
              {/* Location Header */}
              {geoData.location && (
                <div
                  className={`px-3 py-2 text-sm font-semibold flex items-center gap-2 ${
                    darkMode
                      ? "bg-dark-surface text-slate-200"
                      : "bg-gray-50 text-gray-700"
                  }`}
                >
                  <svg
                    className="w-4 h-4"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {geoData.location}
                </div>
              )}
              
              {/* Map Container */}
              <div style={{ height: "300px", width: "100%" }}>
                <LocationMap
                  latitude={geoData.latitude}
                  longitude={geoData.longitude}
                  location={geoData.location}
                  darkMode={darkMode}
                />
              </div>

              {/* Coordinates Footer */}
              <div
                className={`px-3 py-1.5 text-xs flex items-center justify-between ${
                  darkMode
                    ? "bg-dark-surface/50 text-slate-400"
                    : "bg-gray-50/50 text-gray-500"
                }`}
              >
                <span>📍 Coordinates:</span>
                <span className="font-mono">
                  {geoData.latitude.toFixed(4)}, {geoData.longitude.toFixed(4)}
                </span>
              </div>
            </div>
          )}
          {/* Timestamp */}
          <span
            className={`text-[10px] mt-1.5 px-1 font-medium ${
              darkMode ? "text-slate-500" : "text-gray-400/80"
            }`}
          >
            {message.timestamp.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>

          {/* Suggestions */}
          {!isUser && message.suggestions && message.suggestions.length > 0 && (
            <div
              className="mt-3 flex flex-wrap gap-2 animate-enter"
              style={{ animationDelay: "0.1s" }}
            >
              {message.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => onSuggestionClick(suggestion)}
                  className={`px-4 py-1.5 border text-xs font-semibold rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-md backdrop-blur-sm ${
                    darkMode
                      ? "bg-dark-elev/60 hover:bg-dark-elev border-dark-border text-emerald-300"
                      : "bg-white/40 hover:bg-white/80 border-white/50 text-emerald-700"
                  }`}
                >
                  ✨ {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
