import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';

function WebcamFeed({ socket, isAnalyzing, currentPose }) {

  console.log('🎥 WebcamFeed render - Props:', { 
    socket: !!socket, 
    isAnalyzing, 
    currentPose 
  });
  

  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  const [landmarks, setLandmarks] = useState(null);

  // Send frames to backend when analyzing
  useEffect(() => {
    if (!socket || !isAnalyzing) return;

    const interval = setInterval(() => {
      if (webcamRef.current) {
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc) {
          socket.emit('video_frame', {
            image: imageSrc,
            pose_name: currentPose
          });
        }
      }
    }, 100); // Send 10 frames per second

    return () => clearInterval(interval);
  }, [socket, isAnalyzing, currentPose]);

  // Receive landmarks from backend
  useEffect(() => {
    if (!socket) return;

    socket.on('landmarks', (data) => {
      setLandmarks(data.landmarks);
    });

    return () => {
      socket.off('landmarks');
    };
  }, [socket]);

  // Draw skeleton on canvas
  useEffect(() => {
    if (!landmarks || !canvasRef.current || !webcamRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = webcamRef.current.video;

    if (!video) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw connections between landmarks
    const connections = [
      [11, 13], [13, 15], // Left arm
      [12, 14], [14, 16], // Right arm
      [11, 12], // Shoulders
      [11, 23], [12, 24], // Torso
      [23, 24], // Hips
      [23, 25], [25, 27], // Left leg
      [24, 26], [26, 28]  // Right leg
    ];

    // Draw lines
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    connections.forEach(([start, end]) => {
      if (landmarks[start] && landmarks[end]) {
        ctx.beginPath();
        ctx.moveTo(landmarks[start].x * canvas.width, landmarks[start].y * canvas.height);
        ctx.lineTo(landmarks[end].x * canvas.width, landmarks[end].y * canvas.height);
        ctx.stroke();
      }
    });

    // Draw points
    ctx.fillStyle = '#ff0000';
    landmarks.forEach((landmark) => {
      if (landmark) {
        ctx.beginPath();
        ctx.arc(
          landmark.x * canvas.width,
          landmark.y * canvas.height,
          5,
          0,
          2 * Math.PI
        );
        ctx.fill();
      }
    });
  }, [landmarks]);

  return (
    <div className="webcam-container">
      <div className="webcam-wrapper">
        <Webcam
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          videoConstraints={{
            width: 640,
            height: 480,
            facingMode: "user"
          }}
          mirrored={true}
        />
        <canvas
          ref={canvasRef}
          className="overlay-canvas"
        />
      </div>
      
      <div className="status-indicator">
        {isAnalyzing ? (
          <span className="status-active">🟢 Analyzing...</span>
        ) : (
          <span className="status-inactive">⚪ Ready</span>
        )}
      </div>
    </div>
  );
}

export default WebcamFeed;