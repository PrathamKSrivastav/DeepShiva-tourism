import React from 'react';
import { usePdfExport } from '../hooks/usePdfExport';

/**
 * PDF Export Button Component
 * @param {Object} props
 * @param {string} props.sessionId - MongoDB session ID
 * @param {string} props.sessionTitle - Session title for filename
 * @param {string} props.className - Additional CSS classes
 * @param {string} props.variant - 'primary' | 'secondary' | 'icon'
 * @param {boolean} props.darkMode - Dark mode flag
 */
const PdfExportButton = ({ 
  sessionId, 
  sessionTitle = 'Chat',
  className = '',
  variant = 'primary',
  darkMode = false // ← ADDED
}) => {
  const { isLoading, error, downloadPdf } = usePdfExport();

  const handleDownload = async () => {
    if (!sessionId) {
      console.error('❌ No session ID provided');
      return;
    }
    await downloadPdf(sessionId, sessionTitle);
  };

  // ✨ UPDATED: Dark mode aware button styles
  const getButtonStyles = () => {
    const baseStyles = `
      flex items-center justify-center gap-2 rounded-lg font-medium
      transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
      focus:ring-teal-500
    `;

    if (variant === 'icon') {
      return `${baseStyles} p-1.5 ${
        isLoading
          ? darkMode
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          : darkMode
          ? 'bg-gray-700 text-teal-400 hover:bg-gray-600 border border-gray-600'
          : 'bg-white text-teal-600 hover:bg-teal-50 border border-gray-200'
      }`;
    }

    if (variant === 'secondary') {
      return `${baseStyles} px-4 py-2 ${
        isLoading
          ? darkMode
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed border border-gray-600'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          : darkMode
          ? 'bg-gray-800 text-teal-400 border-2 border-teal-500 hover:bg-gray-700'
          : 'bg-white text-teal-600 border-2 border-teal-500 hover:bg-teal-50'
      }`;
    }

    // Primary (default)
    return `${baseStyles} px-4 py-2 ${
      isLoading
        ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
        : 'bg-teal-500 text-white hover:bg-teal-600 active:bg-teal-700 shadow-md hover:shadow-lg'
    }`;
  };

  return (
    <div className={className}>
      <button
        onClick={handleDownload}
        disabled={isLoading}
        className={getButtonStyles()}
        title={isLoading ? 'Generating PDF...' : 'Download as PDF'}
        aria-label="Download PDF"
      >
        {isLoading ? (
          <>
            {/* Loading Spinner */}
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {variant !== 'icon' && <span>Generating...</span>}
          </>
        ) : (
          <>
            {/* Download Icon */}
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            {variant !== 'icon' && <span>Download PDF</span>}
          </>
        )}
      </button>

      {/* Error Message */}
      {error && (
        <div
          className={`mt-2 p-3 rounded-lg text-sm flex items-start gap-2 ${
            darkMode
              ? 'bg-red-900/30 border border-red-700 text-red-300'
              : 'bg-red-50 border border-red-200 text-red-700'
          }`}
        >
          <svg
            className="h-5 w-5 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-medium">Export Failed</p>
            <p className="text-xs mt-1">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PdfExportButton;
