import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api'

function ConnectionStatus() {
  const { isAuthenticated, user } = useAuth()
  const [status, setStatus] = useState({
    internet_connected: true,
    groq_api_available: true,
    rag_enabled: false,
    recommended_mode: 'online'
  })
  const [isChecking, setIsChecking] = useState(false)

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const checkStatus = async () => {
    setIsChecking(true)
    try {
      const response = await apiClient.get('/connection-status')
      setStatus(response.data)
    } catch (error) {
      console.error('Status check failed:', error)
      setStatus({
        internet_connected: false,
        groq_api_available: false,
        rag_enabled: false,
        recommended_mode: 'offline'
      })
    } finally {
      setIsChecking(false)
    }
  }

  const getStatusColor = () => {
    if (!status.internet_connected) return 'bg-red-500'
    if (!status.groq_api_available) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getStatusText = () => {
    if (!isAuthenticated) return 'Guest Mode'
    if (!status.internet_connected) return 'Offline Mode'
    if (!status.groq_api_available) return 'AI Limited'
    return 'Online'
  }

  const getAuthStatusColor = () => {
    return isAuthenticated ? 'bg-green-500' : 'bg-gray-400'
  }

  return (
    <div className="flex items-center space-x-4">
      {/* API Status */}
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()} ${isChecking ? 'animate-pulse' : ''}`}></div>
        <span className="text-sm text-gray-700">{getStatusText()}</span>
      </div>

      {/* Auth Status */}
      {isAuthenticated && user && (
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>✅</span>
          <span className="hidden md:inline">Logged in</span>
        </div>
      )}

      {/* RAG Status (optional - for admin or debugging) */}
      {status.rag_enabled && (
        <div className="hidden lg:flex items-center space-x-1 text-xs text-purple-600">
          <span>🧠</span>
          <span>RAG Active</span>
        </div>
      )}
    </div>
  )
}

export default ConnectionStatus
