import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './SummaryModal.css';

/**
 * Modal component to display AI-generated summary
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close handler
 * @param {Object} props.summary - Summary data object
 * @param {boolean} props.isGenerating - Loading state
 * @param {string} props.error - Error message
 * @param {Function} props.onDownloadPdf - PDF download handler
 * @param {boolean} props.isDownloading - PDF download loading state
 */
const SummaryModal = ({
  isOpen,
  onClose,
  summary,
  isGenerating,
  error,
  onDownloadPdf,
  isDownloading,
}) => {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="summary-modal-overlay" onClick={onClose}>
      <div 
        className="summary-modal-content" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="summary-modal-header">
          <div className="summary-modal-title">
            <span className="summary-icon">🤖</span>
            <h2>AI-Generated Summary</h2>
          </div>
          <button 
            className="summary-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="summary-modal-body">
          {/* Loading State */}
          {isGenerating && (
            <div className="summary-loading">
              <div className="summary-spinner"></div>
              <p>Analyzing conversation with AI...</p>
              <p className="summary-loading-subtext">
                This may take 10-15 seconds
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !isGenerating && (
            <div className="summary-error">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
              <button 
                className="summary-btn summary-btn-secondary"
                onClick={onClose}
              >
                Close
              </button>
            </div>
          )}

          {/* Summary Content */}
          {summary && !isGenerating && !error && (
            <>
              <div className="summary-metadata">
                <span className="summary-badge">
                  📊 {summary.message_count} messages analyzed
                </span>
                <span className="summary-badge">
                  ⏱️ Generated {new Date(summary.generated_at).toLocaleString()}
                </span>
              </div>

              <div className="summary-content">
                <ReactMarkdown>{summary.summary_content}</ReactMarkdown>
              </div>

              {/* Actions */}
              <div className="summary-actions">
                <button
                  className="summary-btn summary-btn-primary"
                  onClick={onDownloadPdf}
                  disabled={isDownloading}
                >
                  {isDownloading ? (
                    <>
                      <span className="btn-spinner"></span>
                      Generating PDF...
                    </>
                  ) : (
                    <>
                      📥 Download Summary PDF
                    </>
                  )}
                </button>
                <button
                  className="summary-btn summary-btn-secondary"
                  onClick={onClose}
                >
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SummaryModal;
