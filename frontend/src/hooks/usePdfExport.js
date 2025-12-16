import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom hook for PDF export functionality
 * @returns {Object} { isLoading, error, downloadPdf }
 */
export const usePdfExport = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Download chat session as PDF
   * @param {string} sessionId - MongoDB session ID
   * @param {string} sessionTitle - Title for the PDF filename
   */
  const downloadPdf = async (sessionId, sessionTitle) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log(`📥 Downloading PDF for session: ${sessionId}`);

      // Get auth token from localStorage
      const token = localStorage.getItem('app_session_token'); // ✅ Correct key

      
      if (!token) {
        throw new Error('Authentication required. Please log in.');
      }

      // Make API request
      const response = await fetch(
        `${API_URL}/api/chat/sessions/${sessionId}/export/pdf`,
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
          errorData.detail || `PDF export failed: ${response.statusText}`
        );
      }

      // Extract filename from headers
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `${sessionTitle || 'chat_export'}.pdf`;
      
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

      console.log('✅ PDF downloaded successfully:', filename);
      
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      setError(errorMessage);
      console.error('❌ PDF download error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, error, downloadPdf };
};
