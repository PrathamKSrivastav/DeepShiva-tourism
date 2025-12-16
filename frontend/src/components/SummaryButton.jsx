import React from 'react';

/**
 * Button to trigger summary generation
 * @param {Object} props
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.isGenerating - Loading state
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.variant - 'primary' | 'icon'
 */
const SummaryButton = ({ 
  onClick, 
  isGenerating = false, 
  disabled = false,
  variant = 'primary'
}) => {
  if (variant === 'icon') {
    // Icon version for sidebar/compact spaces
    return (
      <button
        onClick={onClick}
        disabled={disabled || isGenerating}
        className="summary-icon-btn"
        title="Generate AI Summary"
        aria-label="Generate AI Summary"
      >
        {isGenerating ? (
          <span className="summary-icon-spinner">⏳</span>
        ) : (
          <span className="summary-icon">🤖</span>
        )}
      </button>
    );
  }

  // Primary button version
  return (
    <button
      onClick={onClick}
      disabled={disabled || isGenerating}
      className="summary-primary-btn"
    >
      {isGenerating ? (
        <>
          <span className="summary-btn-spinner"></span>
          Generating...
        </>
      ) : (
        <>
          <span className="summary-btn-icon">🤖</span>
          Generate AI Summary
        </>
      )}
    </button>
  );
};

export default SummaryButton;
