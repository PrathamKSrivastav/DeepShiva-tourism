import { useState, useEffect } from 'react'

function ContentStats({ ragHealth }) {
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/rag/content-stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center text-gray-500 py-8">
        Failed to load statistics
      </div>
    )
  }

  const collections = stats.collections || {}
  const contentTypes = stats.content_types_distribution || {}

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.total_files || 0}</div>
          <div className="text-sm text-blue-700">PDF & Text Files</div>
        </div>
        <div className="bg-green-50 p-6 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{stats.total_urls || 0}</div>
          <div className="text-sm text-green-700">Web Pages</div>
        </div>
        <div className="bg-purple-50 p-6 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{stats.total_documents || 0}</div>
          <div className="text-sm text-purple-700">Total Documents</div>
        </div>
        <div className="bg-orange-50 p-6 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{Object.keys(collections).length}</div>
          <div className="text-sm text-orange-700">Collections</div>
        </div>
      </div>

      {/* Collections Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Collections Overview</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(collections).map(([name, data]) => (
                <tr key={name}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm font-medium text-gray-900 capitalize">
                        {name.replace('uttarakhand_', '')}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{data.document_count || 0}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {name === 'uttarakhand_general' && 'General tourism information'}
                    {name === 'uttarakhand_spiritual' && 'Spiritual and religious content'}
                    {name === 'uttarakhand_trekking' && 'Adventure and trekking information'}
                    {name === 'uttarakhand_cultural' && 'Cultural heritage and traditions'}
                    {name === 'uttarakhand_government' && 'Official government resources'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Content Distribution Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Content Distribution</h3>
        <div className="space-y-3">
          {Object.entries(contentTypes).map(([type, count]) => {
            const total = Object.values(contentTypes).reduce((sum, val) => sum + val, 0)
            const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0
            
            return (
              <div key={type} className="flex items-center">
                <div className="w-24 text-sm text-gray-600 capitalize">{type}</div>
                <div className="flex-1 mx-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
                <div className="w-16 text-sm text-gray-900 text-right">
                  {count} ({percentage}%)
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Processing History */}
      {stats.processing_history && stats.processing_history.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-3">
              {stats.processing_history.slice(-5).reverse().map((activity, index) => (
                <div key={index} className="flex items-center text-sm">
                  <div className="w-20 text-gray-500">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </div>
                  <div className="flex-1 ml-4 text-gray-900">
                    {activity.action === 'add_pdf' && `📄 Added PDF: ${activity.file}`}
                    {activity.action === 'add_webpage' && `🌐 Added webpage: ${activity.url}`}
                    {activity.action === 'add_text' && `📝 Added text: ${activity.title}`}
                    {activity.chunks && ` (${activity.chunks} chunks)`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
        >
          Refresh Statistics
        </button>
      </div>
    </div>
  )
}

export default ContentStats
