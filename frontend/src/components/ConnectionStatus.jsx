import { useState, useEffect } from 'react'
import { checkConnectionStatus } from '../api'

function ConnectionStatus() {
  const [status, setStatus] = useState({
    internet_connected: true,
    groq_api_available: true,  // Changed from gemini_api_available
    recommended_mode: 'online'
  })
  const [isChecking, setIsChecking] = useState(false)

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const checkStatus = async () => {
    setIsChecking(true)
    try {
      const response = await checkConnectionStatus()
      setStatus(response)
    } catch (error) {
      console.error('Status check failed:', error)
      setStatus({
        internet_connected: false,
        groq_api_available: false,  // Changed
        recommended_mode: 'offline'
      })
    } finally {
      setIsChecking(false)
    }
  }

  const getStatusColor = () => {
    if (!status.internet_connected) return 'bg-red-500'
    if (!status.groq_api_available) return 'bg-yellow-500'  // Changed
    return 'bg-green-500'
  }

  const getStatusText = () => {
    if (!status.internet_connected) return 'Offline Mode'
    if (!status.groq_api_available) return 'AI Limited'  // Changed
    return 'AI Online'
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${isChecking ? 'animate-pulse' : ''}`}></div>
      <span className="text-gray-600 font-medium">
        {getStatusText()}
      </span>
    </div>
  )
}

export default ConnectionStatus
