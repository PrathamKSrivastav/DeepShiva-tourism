import React, { useState, useEffect, useRef } from 'react';

function Timer({ duration, isActive, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(duration);
  const hasCompletedRef = useRef(false);

  useEffect(() => {
    setTimeLeft(duration);
    hasCompletedRef.current = false;
  }, [duration]);

  useEffect(() => {
    if (!isActive) {
      setTimeLeft(duration);
      hasCompletedRef.current = false;
      return;
    }

    if (timeLeft === 0 && !hasCompletedRef.current) {
      hasCompletedRef.current = true;
      onComplete();
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, timeLeft, duration, onComplete]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration > 0 ? ((duration - timeLeft) / duration) * 100 : 0;

  return (
    <div className="timer-container">
      <h3>⏱️ Hold Duration</h3>
      <div className="timer-display">
        <span className="time">{formatTime(timeLeft)}</span>
      </div>
      <div className="timer-progress">
        <div 
          className="timer-progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
      {timeLeft === 0 && <p className="timer-complete">✓ Time Complete!</p>}
    </div>
  );
}

export default Timer;