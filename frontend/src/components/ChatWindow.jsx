import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'
import { sendChatMessage } from '../api'

function ChatWindow({ selectedPersona, personaInfo }) {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    // Welcome message when persona changes
    const welcomeMessages = {
      local_guide: "Hey there! I'm your Local Guide. I've been exploring Uttarakhand for years and know all the insider tips. What brings you to Dev Bhoomi? Planning a Char Dham trip, or looking for some adventure?",
      spiritual_teacher: " Namaste, blessed soul. I am honored to guide you through the spiritual essence of these sacred Himalayas. Each temple, each river, each peak here resonates with divine energy. What aspect of this holy land calls to your heart?",
      trek_companion: " Hey adventure buddy! Ready to explore the mountains? I'm here to help you plan treks, check weather, and keep you safe. Whether it's Valley of Flowers or Kedarnath trek - let's gear up! What's your adventure goal?",
      cultural_expert: " Namaste and welcome! As a Cultural Expert, I'll unveil the rich tapestry of myths, legends, and traditions woven into Uttarakhand's landscape. Every stone here has a story spanning millennia. What cultural aspect would you like to explore?"
    }

    setMessages([{
      id: Date.now(),
      text: welcomeMessages[selectedPersona] || welcomeMessages.local_guide,
      sender: 'bot',
      persona: selectedPersona,
      timestamp: new Date()
    }])
  }, [selectedPersona])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(inputMessage, selectedPersona)
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.response,
        sender: 'bot',
        persona: response.persona,
        intent: response.intent,
        suggestions: response.suggestions,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I'm having trouble connecting right now. Please try again in a moment. ",
        sender: 'bot',
        persona: selectedPersona,
        timestamp: new Date(),
        isError: true
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion)
    inputRef.current?.focus()
  }

  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl flex flex-col h-[700px]">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-t-2xl">
        <div className="flex items-center gap-4">
          <span className="text-5xl">{personaInfo?.avatar || '🧑‍🤝‍🧑'}</span>
          <div>
            <h3 className="text-2xl font-heading font-bold">
              {personaInfo?.name || 'Local Guide'}
            </h3>
            <p className="text-sm text-white/90 mt-1">
              {personaInfo?.description || 'Your guide to Uttarakhand'}
            </p>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50 to-white">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onSuggestionClick={handleSuggestionClick}
          />
        ))}
        
        {isLoading && (
          <div className="flex items-center gap-3 text-gray-500">
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-3 h-3 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-3 h-3 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm italic">
              {personaInfo?.name || 'Guide'} is thinking...
            </span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="p-6 bg-gray-50 border-t border-gray-200 rounded-b-2xl">
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about weather, treks, temples, festivals..."
            className="flex-1 px-6 py-4 border-2 border-gray-300 rounded-full focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-gray-800 placeholder-gray-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-full font-semibold hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-3 text-center">
          Ask about Char Dham, trekking, weather, festivals, or emergency info
        </p>
      </form>
    </div>
  )
}

export default ChatWindow
