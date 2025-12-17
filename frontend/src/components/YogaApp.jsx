import React, { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';
import PoseDetails from './PoseDetails';
import WebcamFeed from './WebcamFeed';
import PoseChecklist from './PoseChecklist';
import Timer from './Timer';
import '../styles/YogaApp.css';

const AVAILABLE_POSES = [
  { id: 'warrior_2', name: 'Warrior II Pose' },
  { id: 'tree_pose', name: 'Tree Pose' },
  { id: 'downward_dog', name: 'Downward-Facing Dog' },
  { id: 'plank', name: 'Plank Pose' },
  { id: 'child_pose', name: "Child's Pose" }
];

function YogaApp() {
  const [socket, setSocket] = useState(null);
  const [currentPose, setCurrentPose] = useState(null);
  const [poseInfo, setPoseInfo] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [feedback, setFeedback] = useState([]);
  const [accuracy, setAccuracy] = useState(0);
  const [timerDuration, setTimerDuration] = useState(0);
  const [timerActive, setTimerActive] = useState(false);
  const [completedPoses, setCompletedPoses] = useState([]);

  // Use refs for values used in socket callbacks
  const currentPoseRef = useRef(currentPose);
  const timerActiveRef = useRef(timerActive);

  // Update refs when values change
  useEffect(() => {
    currentPoseRef.current = currentPose;
  }, [currentPose]);

  useEffect(() => {
    timerActiveRef.current = timerActive;
  }, [timerActive]);

  // Memoize handlePoseCompletion to avoid recreating on every render
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
  }, []); // Empty deps because we use refs

  // Initialize Socket.IO connection
  // Initialize Socket.IO connection
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
      console.log('Transport:', newSocket.io.engine.transport.name);
    });

    newSocket.on('connect_error', (error) => {
      console.error('❌ Connection Error:', error.message);
    });

    newSocket.on('pose_info', (data) => {
      console.log('📋 Pose info received:', data);
      setPoseInfo(data);
      setTimerDuration(data.duration || 30);
    });

    newSocket.on('analysis_started', (data) => {
      console.log('✅ Analysis started confirmation from backend:', data);
    });

    newSocket.on('analysis_stopped', (data) => {
      console.log('⏸️ Analysis stopped confirmation from backend');
    });


    newSocket.on('pose_feedback', (data) => {
      console.log('📊 Feedback received:', data);
      setFeedback(data.feedback || []);
      setAccuracy(data.accuracy || 0);

      if (data.accuracy >= 85 && timerActiveRef.current && currentPoseRef.current) {
        handlePoseCompletion();
      }
    });

    newSocket.on('landmarks', (data) => {
      console.log('🎯 Landmarks received');
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
    
    if (!socket) {
      console.error('❌ Socket not available');
      return;
    }

    if (!socket.connected) {
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

  const handleStartAnalysis = () => {
    console.log('🎯 START BUTTON CLICKED!');
    
    const testPose = 'warrior_2';
    setCurrentPose(testPose);
    
    console.log('Socket exists:', !!socket);
    console.log('Socket connected:', socket?.connected);
    
    if (!socket || !socket.connected) {
      alert('Socket not connected! Check if backend is running on port 5000');
      return;
    }

    // FIX: Set timer duration BEFORE activating
    if (!timerDuration || timerDuration === 0) {
      setTimerDuration(30); // Default 30 seconds
    }

    setIsAnalyzing(true);
    setTimerActive(true);

    console.log('✅ Set isAnalyzing to TRUE');
    console.log('✅ Set timerActive to TRUE');

    console.log('📤 Emitting start_analysis...');
    socket.emit('start_analysis', { pose_name: testPose });

    console.log('Analysis started! Check the console and backend terminal.');
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

  const togglePoseComplete = (poseId) => {
    setCompletedPoses(prev => {
      if (prev.includes(poseId)) {
        return prev.filter(id => id !== poseId);
      } else {
        return [...prev, poseId];
      }
    });
  };

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
          
          <Timer 
            duration={timerDuration}
            isActive={timerActive}
            onComplete={handleTimerComplete}
          />

          <div className="controls">
            <button 
              className="btn btn-start"
              onClick={handleStartAnalysis}
              style={{
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                color: 'white',
                padding: '1rem',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              START ANALYSIS
            </button>
            
            <button 
              className="btn btn-stop"
              onClick={handleStopAnalysis}
              style={{
                background: '#f44336',
                color: 'white',
                padding: '1rem',
                border: 'none',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              STOP
            </button>
          </div>
            

          <PoseChecklist 
            poses={AVAILABLE_POSES}
            currentPose={currentPose}
            completedPoses={completedPoses}
            onPoseSelect={handlePoseSelect}
            onToggleComplete={togglePoseComplete}
          />
        </div>

        <div className="right-panel">
          <WebcamFeed 
            socket={socket}
            isAnalyzing={isAnalyzing}
            currentPose={currentPose}
          />
        </div>
      </div>
    </div>
  );
}

export default YogaApp;