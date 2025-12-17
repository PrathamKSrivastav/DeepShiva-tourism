import React, { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';
import PoseDetails from './PoseDetails';
import WebcamFeed from './WebcamFeed';
import PoseSelector from './PoseSelector';
import Timer from './Timer';
import '../styles/YogaApp.css';

const AVAILABLE_POSES = [
  { id: 't_pose', name: 'T-Pose', category: 'Calibration' },
  { id: 'trikonasana', name: 'Triangle Pose', category: 'Standing' },
  { id: 'virabhadrasana', name: 'Warrior I', category: 'Standing' },
  { id: 'warrior_2', name: 'Warrior II', category: 'Standing' },
  { id: 'vrikshasana', name: 'Tree Pose', category: 'Balance' },
  { id: 'naukasana', name: 'Boat Pose', category: 'Core' },
  { id: 'bhujangasana', name: 'Cobra Pose', category: 'Prone' },
  { id: 'chakrasana', name: 'Wheel Pose', category: 'Backbend' },
  { id: 'balasana', name: "Child's Pose", category: 'Resting' },
  { id: 'sukhasana', name: 'Easy Pose', category: 'Seated' },
  { id: 'shavasana', name: 'Corpse Pose', category: 'Resting' }
];

function YogaApp() {
  const [socket, setSocket] = useState(null);
  const [currentPose, setCurrentPose] = useState(null);
  const [poseInfo, setPoseInfo] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [feedback, setFeedback] = useState([]);
  const [accuracy, setAccuracy] = useState(0);
  const [timerDuration, setTimerDuration] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [completedPoses, setCompletedPoses] = useState([]);

  const currentPoseRef = useRef(currentPose);
  const timerActiveRef = useRef(timerActive);
  const accuracyRef = useRef(accuracy);

  useEffect(() => {
    currentPoseRef.current = currentPose;
  }, [currentPose]);

  useEffect(() => {
    timerActiveRef.current = timerActive;
  }, [timerActive]);

  useEffect(() => {
    accuracyRef.current = accuracy;
  }, [accuracy]);

  const handlePoseCompletion = useCallback(() => {
    const pose = currentPoseRef.current;
    setCompletedPoses(prev => {
      if (pose && !prev.includes(pose)) {
        return [...prev, pose];
      }
      return prev;
    });
    setIsAnalyzing(false);
    setTimerActive(false);
    
    // Auto-advance to next pose if accuracy was good
    if (accuracyRef.current >= 85) {
      const currentIndex = AVAILABLE_POSES.findIndex(p => p.id === pose);
      if (currentIndex < AVAILABLE_POSES.length - 1) {
        const nextPose = AVAILABLE_POSES[currentIndex + 1];
        setTimeout(() => {
          handlePoseSelect(nextPose.id);
        }, 2000);
      }
    }
  }, []);

  // Initialize Socket.IO connection
  useEffect(() => {
    console.log('🔌 Initializing socket connection...');
    
    const newSocket = io('http://localhost:5000', {
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000
    });

    newSocket.on('connect', () => {
      console.log('✅ Connected to Flask server');
      console.log('Socket ID:', newSocket.id);
    });

    newSocket.on('connect_error', (error) => {
      console.error('❌ Connection Error:', error.message);
    });

    newSocket.on('error', (data) => {
      console.error('❌ Socket Error:', data);
      alert(`Error: ${data.message || 'Unknown error'}`);
    });


    newSocket.on('pose_info', (data) => {
      console.log('📋 Pose info received:', data);
      setPoseInfo(data);
      setTimerDuration(data.duration || 30);
    });

    newSocket.on('pose_feedback', (data) => {
      setFeedback(data.feedback || []);
      setAccuracy(data.accuracy || 0);
    });

    newSocket.on('landmarks', (data) => {
      // Landmarks received for skeleton drawing
    });

    newSocket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from server. Reason:', reason);
    });

    setSocket(newSocket);

    return () => {
      console.log('🔌 Closing socket connection');
      newSocket.close();
    };
  }, [handlePoseCompletion]);

  const handlePoseSelect = (poseId) => {
    console.log('🎯 Pose selected:', poseId);
    
    if (!socket || !socket.connected) {
      console.error('❌ Socket not connected');
      return;
    }
    
    setCurrentPose(poseId);
    setIsAnalyzing(false);
    setTimerActive(false);
    setFeedback([]);
    setAccuracy(0);

    console.log('📤 Requesting pose info for:', poseId);
    socket.emit('get_pose_info', { pose_name: poseId });
  };

  const handleGetStarted = () => {
    if (!currentPose) {
      alert('Please select a pose first!');
      return;
    }
    
    if (!socket || !socket.connected) {
      alert('Socket not connected! Check if backend is running on port 5000');
      return;
    }
    
    setIsInitialized(true);
    console.log('✅ Webcam initialized, ready for analysis');
  };

  const handleRunAnalysis = () => {
    if (!currentPose) {
      alert('Please select a pose first!');
      return;
    }

    setIsAnalyzing(true);
    setTimerActive(true);
    
    console.log('📤 Emitting start_analysis for:', currentPose);
    socket.emit('start_analysis', { pose_name: currentPose });
  };

  const handleStopAnalysis = () => {
    setIsAnalyzing(false);
    setTimerActive(false);
    
    if (socket) {
      socket.emit('stop_analysis');
    }
  };

  const handleTimerComplete = () => {
    handlePoseCompletion();
  };

  const getButtonConfig = () => {
    if (!isInitialized) {
      return {
        text: 'Get Started',
        action: handleGetStarted,
        className: 'btn-get-started'
      };
    }
    
    if (isAnalyzing) {
      return {
        text: 'Stop Analysis',
        action: handleStopAnalysis,
        className: 'btn-stop'
      };
    }
    
    return {
      text: 'Run Analysis',
      action: handleRunAnalysis,
      className: 'btn-run'
    };
  };

  const buttonConfig = getButtonConfig();

  return (
    <div className="yoga-app">
      <header className="app-header">
        <h1>🧘‍♀️ AI Yoga Trainer</h1>
        <p>Real-time Pose Detection & Correction</p>
      </header>

      <div className="main-container">
        <div className="left-panel">
          <PoseDetails 
            poseInfo={poseInfo}
            currentPose={currentPose}
            feedback={feedback}
            accuracy={accuracy}
          />
          
          {currentPose && (
            <>
              <Timer 
                duration={timerDuration}
                isActive={timerActive}
                onComplete={handleTimerComplete}
              />

              <div className="controls">
                <button 
                  className={`btn ${buttonConfig.className}`}
                  onClick={buttonConfig.action}
                  disabled={!currentPose}
                >
                  {buttonConfig.text}
                </button>
              </div>
            </>
          )}

          <PoseSelector 
            poses={AVAILABLE_POSES}
            currentPose={currentPose}
            completedPoses={completedPoses}
            onPoseSelect={handlePoseSelect}
          />
        </div>

        <div className="right-panel">
          <WebcamFeed 
            socket={socket}
            isAnalyzing={isAnalyzing}
            isInitialized={isInitialized}
            currentPose={currentPose}
          />
        </div>
      </div>
    </div>
  );
}

export default YogaApp;