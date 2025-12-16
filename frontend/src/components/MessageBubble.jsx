import React from "react";

function MessageBubble({ message, onSuggestionClick }) {
  const isUser = message.sender === "user";

  return (
    <div
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      } mb-6 animate-enter`}
    >
      <div
        className={`max-w-[85%] md:max-w-[70%] flex flex-col ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {!isUser && message.persona && (
          <span className="text-[10px] uppercase tracking-wider text-gray-500/80 mb-1 ml-2 font-bold">
            {message.persona.replace("_", " ")}
          </span>
        )}

        {/* Message Bubble */}
        <div
          className={`relative px-5 py-3.5 text-[15px] leading-relaxed shadow-sm backdrop-blur-md border 
            ${
              isUser
                ? // UPDATED: More Subtle Gradient (Purple/Indigo - 500 level)
                  // Changed from red-600/purple-700/indigo-600 to purple-500/indigo-500
                  "bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-xl rounded-br-none border-white/30 shadow-indigo-500/30"
                : message.isError
                ? "bg-red-50/90 text-red-800 rounded-2xl rounded-bl-sm border-red-200"
                : "bg-white/60 hover:bg-white/70 transition-colors text-gray-800 rounded-2xl rounded-bl-sm border-white/40 shadow-gray-900/5"
            }`}
        >
          <p className="whitespace-pre-wrap font-normal">{message.text}</p>
        </div>

        {/* Timestamp */}
        <span className="text-[10px] mt-1.5 px-1 font-medium text-gray-400/80">
          {message.timestamp.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>

        {/* Suggestions - Now more playful */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <div
            className="mt-3 flex flex-wrap gap-2 animate-enter"
            style={{ animationDelay: "0.1s" }}
          >
            {message.suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSuggestionClick(suggestion)}
                className="px-4 py-1.5 bg-white/40 hover:bg-white/80 border border-white/50 text-purple-800 text-xs font-semibold rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-md backdrop-blur-sm"
              >
                ✨ {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
