import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MessageBubble({ message, onSuggestionClick, darkMode }) {
  const isUser = message.sender === "user";

  // Clean JSON code blocks from message text for display
  const cleanText = message.text.replace(/```json[\s\S]*?```/g, "").trim();

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
                ? "bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-xl rounded-br-none border-white/30 shadow-indigo-500/30"
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
                  // Customize markdown elements for better styling
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
                            ? "bg-dark-surface text-indigo-300"
                            : "bg-indigo-100 text-indigo-800"
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
                          ? "text-indigo-300 hover:text-indigo-200"
                          : "text-indigo-600 hover:text-indigo-800"
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
                          ? "border-indigo-500 text-slate-300"
                          : "border-indigo-400 text-gray-700"
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
                    ? "bg-dark-elev/60 hover:bg-dark-elev border-dark-border text-indigo-300"
                    : "bg-white/40 hover:bg-white/80 border-white/50 text-purple-800"
                }`}
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
