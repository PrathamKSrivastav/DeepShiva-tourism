import { useState } from 'react'

function SearchTest() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedCollections, setSelectedCollections] = useState([])
  const [maxResults, setMaxResults] = useState(5)

  const collections = [
    'india_general',
    'india_spiritual', 
    'india_trekking',
    'india_cultural',
    'india_government'
  ]

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const params = new URLSearchParams({
        query: query,
        n_results: maxResults.toString()
      })

      if (selectedCollections.length > 0) {
        selectedCollections.forEach(collection => {
          params.append('collection_names', collection)
        })
      }

      const response = await fetch(`http://localhost:8000/api/rag/test-search?${params}`)
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error searching:', error)
      setResults({ error: error.message })
    } finally {
      setIsSearching(false)
    }
  }

  const handleCollectionToggle = (collection) => {
    setSelectedCollections(prev => 
      prev.includes(collection)
        ? prev.filter(c => c !== collection)
        : [...prev, collection]
    )
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Query
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Collections to Search
            </label>
            <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-md p-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="all-collections"
                  checked={selectedCollections.length === 0}
                  onChange={() => setSelectedCollections([])}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="all-collections" className="ml-2 text-sm text-gray-700">
                  All Collections
                </label>
              </div>
              {collections.map((collection) => (
                <div key={collection} className="flex items-center">
                  <input
                    type="checkbox"
                    id={collection}
                    checked={selectedCollections.includes(collection)}
                    onChange={() => handleCollectionToggle(collection)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor={collection} className="ml-2 text-sm text-gray-700 capitalize">
                    {collection.replace('india_', '')}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Results
            </label>
            <input
              type="number"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value) || 5)}
              min="1"
              max="20"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isSearching ? 'Searching...' : 'Search Documents'}
        </button>
      </form>

      {/* Search Results */}
      {results && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Search Results
              {results.total_results && (
                <span className="ml-2 text-sm text-gray-500">
                  ({results.total_results} results found)
                </span>
              )}
            </h3>
          </div>
          <div className="px-6 py-4">
            {results.error ? (
              <div className="text-red-600">Error: {results.error}</div>
            ) : results.results ? (
              <div className="space-y-6">
                {Object.entries(results.results).map(([collection, docs]) => (
                  <div key={collection}>
                    <h4 className="font-medium text-gray-900 mb-3 capitalize">
                      {collection.replace('india_', '')} Collection ({docs.length} results)
                    </h4>
                    <div className="space-y-3">
                      {docs.map((doc, index) => (
                        <div
                          key={index}
                          className="p-4 border border-gray-200 rounded-lg"
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="text-sm text-gray-500">
                              Similarity: {((1 - (doc.distance || 0)) * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-400">
                              {doc.metadata?.source_type || 'Unknown source'}
                            </div>
                          </div>
                          <div className="text-sm text-gray-800 leading-relaxed">
                            {doc.content}
                          </div>
                          {doc.metadata?.title && (
                            <div className="mt-2 text-xs text-gray-600">
                              Source: {doc.metadata.title}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-500">No results to display</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchTest
