import React, { useState, useEffect, useRef } from 'react';

function Timer({ duration, isActive, onComplete }) {
  const [timeLeft, setTimeLeft] = useState(duration);
  const hasStartedRef = useRef(false);

  useEffect(() => {
    setTimeLeft(duration);
    if (isActive) {
      hasStartedRef.current = true;
    }
  }, [duration]);

  useEffect(() => {
    if (!isActive) {
      setTimeLeft(duration);
      hasStartedRef.current = false;
      return;
    }

    // Don't complete if we just started and time is 0
    if (timeLeft === 0) {
      if (hasStartedRef.current) {
        console.log('⏱️ Timer reached 0, calling onComplete');
        onComplete();
      }
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
      <h3>⏱️ Timer</h3>
      <div className="timer-display">
        <span className="time">{formatTime(timeLeft)}</span>
      </div>
      <div className="timer-progress">
        <div 
          className="timer-progress-bar"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

export default Timer;