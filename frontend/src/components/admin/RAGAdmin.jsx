import { useState, useEffect } from 'react'
import ContentUpload from './ContentUpload'
import ContentStats from './ContentStats'
import SearchTest from './SearchTest'

function RAGAdmin() {
  const [activeTab, setActiveTab] = useState('upload')
  const [ragHealth, setRagHealth] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkRagHealth()
  }, [])

  const checkRagHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/rag/health')
      const health = await response.json()
      setRagHealth(health)
    } catch (error) {
      console.error('Error checking RAG health:', error)
      setRagHealth({ status: 'error', error: error.message })
    } finally {
      setIsLoading(false)
    }
  }

  const tabs = [
    { id: 'upload', name: 'Content Upload', icon: '📤' },
    { id: 'stats', name: 'Statistics', icon: '📊' },
    { id: 'search', name: 'Test Search', icon: '🔍' },
  ]

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-gray-600">Loading RAG Admin...</span>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          🧠 RAG Content Manager
        </h1>
        <p className="text-gray-600">
          Manage your knowledge base for Deep Shiva AI Tourism Bot
        </p>
      </div>

      {/* Health Status */}
      <div className="mb-6 p-4 rounded-lg border-l-4 border-l-indigo-500 bg-indigo-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-indigo-800">RAG System Status</h3>
            <p className="text-sm text-indigo-700">
              Status: <span className="font-medium">{ragHealth?.status || 'Unknown'}</span>
              {ragHealth?.vector_store && (
                <> | Collections: {ragHealth.vector_store.collections} | 
                Documents: {ragHealth.vector_store.total_documents}</>
              )}
            </p>
          </div>
          <button
            onClick={checkRagHealth}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
          >
            Refresh Status
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'upload' && (
          <ContentUpload onUploadSuccess={checkRagHealth} />
        )}
        {activeTab === 'stats' && (
          <ContentStats ragHealth={ragHealth} />
        )}
        {activeTab === 'search' && (
          <SearchTest />
        )}
      </div>
    </div>
  )
}

export default RAGAdmin
