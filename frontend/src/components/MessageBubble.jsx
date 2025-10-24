function MessageBubble({ message, onSuggestionClick }) {
  const isUser = message.sender === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message Bubble */}
        <div
          className={`px-6 py-4 rounded-2xl shadow-md ${
            isUser
              ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-none'
              : message.isError
              ? 'bg-red-100 text-red-800 rounded-bl-none border border-red-300'
              : 'bg-white text-gray-800 rounded-bl-none border border-gray-200'
          }`}
        >
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {message.text}
          </p>
          
          {/* Timestamp */}
          <p className={`text-xs mt-2 ${
            isUser ? 'text-white/70' : 'text-gray-500'
          }`}>
            {message.timestamp.toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
        </div>

        {/* Suggestions (only for bot messages) */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs text-gray-500 font-medium px-2">
              💡 You might also ask:
            </p>
            <div className="flex flex-wrap gap-2">
              {message.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => onSuggestionClick(suggestion)}
                  className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm rounded-full border border-indigo-200 transition-all hover:shadow-md transform hover:scale-105 active:scale-95"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
