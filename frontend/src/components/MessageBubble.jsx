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
        {/* Persona Label (Optional, good for group context) */}
        {!isUser && message.persona && (
          <span className="text-[10px] uppercase tracking-wider text-gray-400 mb-1 ml-2 font-semibold">
            {message.persona.replace("_", " ")}
          </span>
        )}

        {/* Message Bubble */}
        <div
          className={`relative px-5 py-3.5 text-[15px] leading-relaxed shadow-sm backdrop-blur-md border 
            ${
              isUser
                ? "bg-gradient-to-br from-indigo-600 to-indigo-500 text-white rounded-2xl rounded-br-sm border-indigo-400/20"
                : message.isError
                ? "bg-red-50/80 text-red-800 rounded-2xl rounded-bl-sm border-red-200"
                : "bg-white/70 text-gray-800 rounded-2xl rounded-bl-sm border-white/50"
            }`}
        >
          <p className="whitespace-pre-wrap font-normal">{message.text}</p>
        </div>

        {/* Timestamp */}
        <span
          className={`text-[10px] mt-1.5 px-1 font-medium ${
            isUser ? "text-gray-400" : "text-gray-400"
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
                className="px-3 py-1.5 bg-white/40 hover:bg-white/80 border border-white/40 text-indigo-700 text-xs font-medium rounded-full transition-all duration-300 transform hover:scale-105 hover:shadow-sm backdrop-blur-sm"
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
