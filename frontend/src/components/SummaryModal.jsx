import React, { useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./SummaryModal.css";

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
 * @param {boolean} props.darkMode - Dark mode flag
 */
const SummaryModal = ({
  isOpen,
  onClose,
  summary,
  isGenerating,
  error,
  onDownloadPdf,
  isDownloading,
  darkMode = false,
}) => {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 animate-fadeIn"
      style={{
        backgroundColor: darkMode ? "rgba(0, 0, 0, 0.7)" : "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        className={`relative w-full max-w-4xl max-h-[90vh] rounded-3xl overflow-hidden shadow-2xl animate-slideUp ${
          darkMode
            ? "bg-dark-surface border border-dark-border"
            : "bg-white/95 backdrop-blur-xl border border-white/40"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative gradient header background */}
        
        {/* Header */}
        <div
          className={`relative z-10 flex items-center justify-between p-6 border-b ${
            darkMode ? "border-dark-border" : "border-white/20"
          }`}
        >
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent-indigo to-accent-fuchsia flex items-center justify-center text-2xl shadow-lg">
              🤖
            </div>
            <div>
              <h2
                className={`text-xl font-bold ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}
              >
                AI-Generated Summary
              </h2>
              <p
                className={`text-sm ${
                  darkMode ? "text-dark-muted" : "text-gray-500"
                }`}
              >
                Powered by advanced AI analysis
              </p>
            </div>
          </div>

          <button
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:scale-110 ${
              darkMode
                ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                : "bg-white/80 hover:bg-white text-gray-700"
            }`}
            onClick={onClose}
            aria-label="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div
          className={`relative overflow-y-auto p-6 ${
            darkMode ? "text-slate-100" : "text-gray-900"
          }`}
          style={{ maxHeight: "calc(90vh - 180px)" }}
        >
          {/* Loading State */}
          {isGenerating && (
            <div className="flex flex-col items-center justify-center py-16 px-4">
              {/* Animated spinner */}
              <div className="relative w-20 h-20 mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-gray-200/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-t-accent-indigo border-r-accent-fuchsia border-b-transparent border-l-transparent animate-spin"></div>
                <div className="absolute inset-2 rounded-full bg-gradient-to-br from-accent-indigo/20 to-accent-fuchsia/20 flex items-center justify-center">
                  <span className="text-2xl animate-pulse">🤖</span>
                </div>
              </div>

              <p
                className={`text-lg font-semibold mb-2 ${
                  darkMode ? "text-white" : "text-gray-900"
                }`}
              >
                Analyzing conversation with AI
              </p>

              {/* Enhanced Loading Bar */}
              <div className="w-full max-w-md mt-8 mb-4">
                <div
                  className={`relative h-2 rounded-full overflow-hidden ${
                    darkMode ? "bg-dark-elev" : "bg-gray-200"
                  }`}
                >
                  <div
                    className="absolute inset-0 rounded-full animate-progressSlide"
                    style={{
                      background:
                        "linear-gradient(90deg, #6366f1, #a855f7, #ec4899)",
                      backgroundSize: "200% 100%",
                      boxShadow: "0 0 20px rgba(99, 102, 241, 0.5)",
                    }}
                  />
                  <div
                    className="absolute inset-0 animate-shimmer"
                    style={{
                      background:
                        "linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)",
                      backgroundSize: "200% 100%",
                    }}
                  />
                </div>
                <p
                  className={`text-xs text-center mt-3 ${
                    darkMode ? "text-dark-muted" : "text-gray-500"
                  }`}
                >
                  Processing messages...
                </p>
              </div>

              <p
                className={`text-sm ${
                  darkMode ? "text-dark-muted" : "text-gray-600"
                }`}
              >
                This may take 10-15 seconds
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !isGenerating && (
            <div className="flex flex-col items-center justify-center py-16 px-4">
              <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center mb-4">
                <span className="text-3xl">⚠️</span>
              </div>
              <p className="text-red-600 dark:text-red-400 text-center mb-6 max-w-md">
                {error}
              </p>
              <button
                className={`px-6 py-3 rounded-xl font-medium transition-all ${
                  darkMode
                    ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                    : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                }`}
                onClick={onClose}
              >
                Close
              </button>
            </div>
          )}

          {/* Summary Content */}
          {summary && !isGenerating && !error && (
            <>
              {/* Metadata badges */}
              <div className="flex flex-wrap gap-2 mb-6">
                <span
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${
                    darkMode
                      ? "bg-accent-indigo/10 text-accent-indigo border border-accent-indigo/20"
                      : "bg-indigo-50 text-indigo-700 border border-indigo-200"
                  }`}
                >
                  <span>📊</span>
                  {summary.message_count} messages
                </span>
                <span
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${
                    darkMode
                      ? "bg-accent-fuchsia/10 text-accent-fuchsia border border-accent-fuchsia/20"
                      : "bg-pink-50 text-pink-700 border border-pink-200"
                  }`}
                >
                  <span>⏱️</span>
                  {new Date(summary.generated_at).toLocaleString()}
                </span>
              </div>

              {/* Summary text with markdown */}
              <div
                className={`prose max-w-none ${darkMode ? "prose-invert" : ""}`}
              >
                <div
                  className={`leading-relaxed space-y-4 ${
                    darkMode ? "text-slate-200" : "text-gray-700"
                  }`}
                >
                  <ReactMarkdown
                    components={{
                      h1: ({ node, ...props }) => (
                        <h1
                          className="text-2xl font-bold mb-4 bg-gradient-to-r from-accent-indigo to-accent-fuchsia bg-clip-text text-transparent"
                          {...props}
                        />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2
                          className="text-xl font-semibold mt-6 mb-3"
                          {...props}
                        />
                      ),
                      h3: ({ node, ...props }) => (
                        <h3
                          className="text-lg font-semibold mt-4 mb-2"
                          {...props}
                        />
                      ),
                      p: ({ node, ...props }) => (
                        <p className="mb-4" {...props} />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul
                          className="list-disc list-inside space-y-2 mb-4"
                          {...props}
                        />
                      ),
                      ol: ({ node, ...props }) => (
                        <ol
                          className="list-decimal list-inside space-y-2 mb-4"
                          {...props}
                        />
                      ),
                      li: ({ node, ...props }) => (
                        <li className="ml-4" {...props} />
                      ),
                      strong: ({ node, ...props }) => (
                        <strong
                          className="font-semibold text-accent-indigo"
                          {...props}
                        />
                      ),
                      code: ({ node, inline, ...props }) =>
                        inline ? (
                          <code
                            className={`px-2 py-1 rounded text-sm ${
                              darkMode
                                ? "bg-dark-elev text-accent-fuchsia"
                                : "bg-gray-100 text-pink-600"
                            }`}
                            {...props}
                          />
                        ) : (
                          <code
                            className={`block p-4 rounded-lg text-sm ${
                              darkMode ? "bg-dark-elev" : "bg-gray-100"
                            }`}
                            {...props}
                          />
                        ),
                    }}
                  >
                    {summary.summary_content}
                  </ReactMarkdown>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-dark-border">
                <button
                  className="flex-1 px-6 py-3 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  style={{
                    background:
                      "linear-gradient(135deg, #6366f1 0%, #d946ef 100%)",
                    color: "white",
                    boxShadow: "0 4px 14px rgba(99, 102, 241, 0.3)",
                  }}
                  onClick={onDownloadPdf}
                  disabled={isDownloading}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.transform = "translateY(-2px)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.transform = "translateY(0)")
                  }
                >
                  {isDownloading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Generating PDF...</span>
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span>Download PDF</span>
                    </>
                  )}
                </button>
                <button
                  className={`px-6 py-3 rounded-xl font-medium transition-all ${
                    darkMode
                      ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                  }`}
                  onClick={onClose}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.transform = "translateY(-2px)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.transform = "translateY(0)")
                  }
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
