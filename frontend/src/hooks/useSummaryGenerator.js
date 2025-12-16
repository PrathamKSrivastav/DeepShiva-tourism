import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom hook for generating and managing chat summaries
 * @returns {Object} { isGenerating, error, summary, generateSummary, downloadSummaryPdf, clearSummary }
 */
export const useSummaryGenerator = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);

  /**
   * Generate AI summary for a chat session
   * @param {string} sessionId - MongoDB session ID
   */
  const generateSummary = async (sessionId) => {
    setIsGenerating(true);
    setError(null);
    setSummary(null);

    try {
      console.log(`🤖 Generating summary for session: ${sessionId}`);

      const token = localStorage.getItem('app_session_token');
      
      if (!token) {
        throw new Error('Authentication required. Please log in.');
      }

      // Call summary generation endpoint
      const response = await fetch(
        `${API_URL}/api/chat/sessions/${sessionId}/summary`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Summary generation failed: ${response.statusText}`
        );
      }

      const data = await response.json();
      
      console.log('✅ Summary generated successfully');
      setSummary(data.summary);
      
      return data.summary;
      
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      setError(errorMessage);
      console.error('❌ Summary generation error:', err);
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Download summary as PDF
   * @param {string} sessionId - MongoDB session ID
   * @param {string} sessionTitle - Title for filename
   */
  const downloadSummaryPdf = async (sessionId, sessionTitle) => {
    setIsDownloading(true);
    setError(null);

    try {
      console.log(`📥 Downloading summary PDF for session: ${sessionId}`);

      const token = localStorage.getItem('app_session_token');
      
      if (!token) {
        throw new Error('Authentication required. Please log in.');
      }

      // Download PDF
      const response = await fetch(
        `${API_URL}/api/chat/sessions/${sessionId}/summary/pdf`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `PDF download failed: ${response.statusText}`
        );
      }

      // Extract filename from headers
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `Summary_${sessionTitle || 'chat'}.pdf`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Create blob and trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }, 100);

      console.log('✅ Summary PDF downloaded successfully:', filename);
      
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      setError(errorMessage);
      console.error('❌ PDF download error:', err);
      throw err;
    } finally {
      setIsDownloading(false);
    }
  };

  /**
   * Fetch existing summary without regenerating
   * @param {string} sessionId - MongoDB session ID
   */
  const fetchExistingSummary = async (sessionId) => {
    try {
      const token = localStorage.getItem('app_session_token');
      
      if (!token) {
        return null;
      }

      const response = await fetch(
        `${API_URL}/api/chat/sessions/${sessionId}/summary`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSummary(data.summary);
        return data.summary;
      }
      
      return null;
      
    } catch (err) {
      console.log('No existing summary found');
      return null;
    }
  };

  /**
   * Clear current summary from state
   */
  const clearSummary = () => {
    setSummary(null);
    setError(null);
  };

  return {
    isGenerating,
    isDownloading,
    error,
    summary,
    generateSummary,
    downloadSummaryPdf,
    fetchExistingSummary,
    clearSummary,
  };
};
