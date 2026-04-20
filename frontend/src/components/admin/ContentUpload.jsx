import { useState, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function ContentUpload({ onUploadSuccess }) {
  const [uploadType, setUploadType] = useState('pdf')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const fileInputRef = useRef(null)

  // Form states
  const [pdfFile, setPdfFile] = useState(null)
  const [webUrl, setWebUrl] = useState('')
  const [textTitle, setTextTitle] = useState('')
  const [textContent, setTextContent] = useState('')
  const [contentType, setContentType] = useState('general')
  const [batchDirectory, setBatchDirectory] = useState('')

  const contentTypes = [
    { id: 'general', name: 'General Tourism' },
    { id: 'spiritual', name: 'Spiritual & Religious' },
    { id: 'trekking', name: 'Trekking & Adventure' },
    { id: 'cultural', name: 'Cultural & Heritage' },
    { id: 'government', name: 'Government & Official' }
  ]

  const handlePdfUpload = async (e) => {
    e.preventDefault()
    if (!pdfFile) return

    setIsUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', pdfFile)
      formData.append('content_type', contentType)

      const response = await fetch(`${API_BASE}/rag/upload-pdf`, {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (response.ok) {
        setUploadResult({ success: true, ...result })
        setPdfFile(null)
        fileInputRef.current.value = ''
        onUploadSuccess?.()
      } else {
        setUploadResult({ success: false, error: result.detail || 'Upload failed' })
      }
    } catch (error) {
      setUploadResult({ success: false, error: error.message })
    } finally {
      setIsUploading(false)
    }
  }

  const handleWebPageAdd = async (e) => {
    e.preventDefault()
    if (!webUrl) return

    setIsUploading(true)
    setUploadResult(null)

    try {
      const response = await fetch(`${API_BASE}/rag/add-webpage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: webUrl,
          content_type: contentType
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setUploadResult({ success: true, ...result })
        setWebUrl('')
        onUploadSuccess?.()
      } else {
        setUploadResult({ success: false, error: result.detail || 'Failed to add web page' })
      }
    } catch (error) {
      setUploadResult({ success: false, error: error.message })
    } finally {
      setIsUploading(false)
    }
  }

  const handleTextAdd = async (e) => {
    e.preventDefault()
    if (!textTitle || !textContent) return

    setIsUploading(true)
    setUploadResult(null)

    try {
      const response = await fetch(`${API_BASE}/rag/add-text-content`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: textTitle,
          content: textContent,
          content_type: contentType
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setUploadResult({ success: true, ...result })
        setTextTitle('')
        setTextContent('')
        onUploadSuccess?.()
      } else {
        setUploadResult({ success: false, error: result.detail || 'Failed to add text content' })
      }
    } catch (error) {
      setUploadResult({ success: false, error: error.message })
    } finally {
      setIsUploading(false)
    }
  }

  const handleBatchProcess = async (e) => {
    e.preventDefault()
    if (!batchDirectory) return

    setIsUploading(true)
    setUploadResult(null)

    try {
      const response = await fetch(`${API_BASE}/rag/batch-process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          directory_path: batchDirectory,
          content_type: contentType
        }),
      })

      const result = await response.json()

      if (response.ok) {
        setUploadResult({ success: true, ...result })
        setBatchDirectory('')
        onUploadSuccess?.()
      } else {
        setUploadResult({ success: false, error: result.detail || 'Batch processing failed' })
      }
    } catch (error) {
      setUploadResult({ success: false, error: error.message })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Type Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Choose Upload Type
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { id: 'pdf', name: 'PDF File', icon: '📄' },
            { id: 'webpage', name: 'Web Page', icon: '🌐' },
            { id: 'text', name: 'Text Content', icon: '📝' },
            { id: 'batch', name: 'Batch Process', icon: '📁' }
          ].map((type) => (
            <button
              key={type.id}
              onClick={() => setUploadType(type.id)}
              className={`p-4 rounded-lg border-2 text-center transition-colors ${
                uploadType === type.id
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="text-2xl mb-2">{type.icon}</div>
              <div className="text-sm font-medium">{type.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Content Type Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Content Category
        </label>
        <select
          value={contentType}
          onChange={(e) => setContentType(e.target.value)}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        >
          {contentTypes.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </select>
      </div>

      {/* Upload Forms */}
      {uploadType === 'pdf' && (
        <form onSubmit={handlePdfUpload} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select PDF File
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={(e) => setPdfFile(e.target.files[0])}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isUploading || !pdfFile}
            className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isUploading ? 'Uploading...' : 'Upload PDF'}
          </button>
        </form>
      )}

      {uploadType === 'webpage' && (
        <form onSubmit={handleWebPageAdd} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website URL
            </label>
            <input
              type="url"
              value={webUrl}
              onChange={(e) => setWebUrl(e.target.value)}
              placeholder="https://example.com"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Add official India's government websites or verified tourism sources
            </p>
          </div>
          <button
            type="submit"
            disabled={isUploading || !webUrl}
            className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isUploading ? 'Processing...' : 'Add Web Page'}
          </button>
        </form>
      )}

      {uploadType === 'text' && (
        <form onSubmit={handleTextAdd} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content Title
            </label>
            <input
              type="text"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Enter a descriptive title"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Content
            </label>
            <textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              rows={8}
              placeholder="Paste your content here..."
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={isUploading || !textTitle || !textContent}
            className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isUploading ? 'Adding...' : 'Add Text Content'}
          </button>
        </form>
      )}

      {uploadType === 'batch' && (
        <form onSubmit={handleBatchProcess} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Directory Path
            </label>
            <input
              type="text"
              value={batchDirectory}
              onChange={(e) => setBatchDirectory(e.target.value)}
              placeholder="C:/path/to/your/documents"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Directory containing PDFs and text files to process
            </p>
          </div>
          <button
            type="submit"
            disabled={isUploading || !batchDirectory}
            className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isUploading ? 'Processing...' : 'Start Batch Processing'}
          </button>
        </form>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <div className={`p-4 rounded-md ${
          uploadResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {uploadResult.success ? (
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <h3 className={`text-sm font-medium ${
                uploadResult.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {uploadResult.success ? 'Success!' : 'Error'}
              </h3>
              <div className={`mt-2 text-sm ${
                uploadResult.success ? 'text-green-700' : 'text-red-700'
              }`}>
                {uploadResult.success ? (
                  <div>
                    {uploadResult.message && <p>{uploadResult.message}</p>}
                    {uploadResult.chunks_count && (
                      <p>Processed {uploadResult.chunks_count} document chunks</p>
                    )}
                    {uploadResult.collection && (
                      <p>Added to '{uploadResult.collection}' collection</p>
                    )}
                    {uploadResult.processed_files && (
                      <p>Processed {uploadResult.processed_files.length} files successfully</p>
                    )}
                  </div>
                ) : (
                  <p>{uploadResult.error}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ContentUpload
