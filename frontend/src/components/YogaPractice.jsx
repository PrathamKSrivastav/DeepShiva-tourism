import React, { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Webcam from "react-webcam";
import { useYoga } from "../hooks/useYoga";

const YogaPractice = ({ poseName, poseDetails, onClose, darkMode }) => {
  const [capturedImage, setCapturedImage] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [useWebcam, setUseWebcam] = useState(false);
  const [isRealtimeMode, setIsRealtimeMode] = useState(false);
  const [realtimeFeedback, setRealtimeFeedback] = useState(null);
  const [landmarks, setLandmarks] = useState([]);
  const [frameCount, setFrameCount] = useState(0);
  const [webcamReady, setWebcamReady] = useState(false);
  const [pendingStart, setPendingStart] = useState(false);

  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);
  const frameIntervalRef = useRef(null);

  const {
    analyzePose,
    connectWebSocket,
    disconnectWebSocket,
    onWebSocketMessage,
    startRealtimeAnalysis,
    stopRealtimeAnalysis,
    sendFrame,
    isConnected,
    isLoading,
    error,
  } = useYoga();

  // Log state changes for debugging
  useEffect(() => {
    console.log("🔍 [STATE] useWebcam:", useWebcam, "| isRealtimeMode:", isRealtimeMode, "| webcamReady:", webcamReady, "| isConnected:", isConnected);
  }, [useWebcam, isRealtimeMode, webcamReady, isConnected]);

  // Cleanup WebSocket when component unmounts or real-time mode ends
  useEffect(() => {
    return () => {
      if (isRealtimeMode) {
        console.log("🔌 [WEBSOCKET] Cleanup - disconnecting");
        stopRealtimeAnalysis();
        disconnectWebSocket();
      }
    };
  }, [isRealtimeMode, stopRealtimeAnalysis, disconnectWebSocket]);

  // Start analysis when WebSocket connects (if pending)
  useEffect(() => {
    if (isConnected && pendingStart && isRealtimeMode) {
      console.log("🎯 [AUTO START] WebSocket connected, starting analysis for:", poseName);
      setPendingStart(false);
      startRealtimeAnalysis(poseName);
    }
  }, [isConnected, pendingStart, isRealtimeMode, poseName, startRealtimeAnalysis]);

  // Setup WebSocket message listeners
  useEffect(() => {
    // Listen for connection confirmation
    const unsubConnected = onWebSocketMessage("connected", (data) => {
      console.log("✅ WebSocket connected:", data);
    });

    // Listen for analysis started
    const unsubStarted = onWebSocketMessage("analysis_started", (data) => {
      console.log("🎯 Analysis started:", data);
      setIsAnalyzing(true);
    });

    // Listen for landmarks
    const unsubLandmarks = onWebSocketMessage("landmarks", (data) => {
      setLandmarks(data.landmarks || []);
    });

    // Listen for feedback
    const unsubFeedback = onWebSocketMessage("feedback", (data) => {
      setRealtimeFeedback(data.data);
      setFrameCount((prev) => prev + 1);
    });

    // Listen for analysis stopped
    const unsubStopped = onWebSocketMessage("analysis_stopped", () => {
      console.log("⏸️ Analysis stopped");
      setIsAnalyzing(false);
    });

    // Listen for errors
    const unsubError = onWebSocketMessage("error", (data) => {
      console.error("❌ WebSocket error:", data.message);
      alert(`Error: ${data.message}`);
    });

    // Cleanup listeners
    return () => {
      unsubConnected();
      unsubStarted();
      unsubLandmarks();
      unsubFeedback();
      unsubStopped();
      unsubError();
    };
  }, [onWebSocketMessage]);

  // Real-time frame capture and send
  useEffect(() => {
    console.log("📹 [FRAME EFFECT] Conditions:", {
      isRealtimeMode,
      useWebcam,
      webcamReady,
      hasWebcamRef: !!webcamRef.current
    });

    if (isRealtimeMode && useWebcam && webcamReady && webcamRef.current) {
      console.log("📹 [FRAME CAPTURE] Starting frame capture at 10 FPS");
      
      // Wait a moment for webcam to fully stabilize
      const startDelay = setTimeout(() => {
        console.log("📹 [FRAME CAPTURE] Delay complete, setting up interval");
        let framesSent = 0;
        
        frameIntervalRef.current = setInterval(() => {
          const imageSrc = webcamRef.current?.getScreenshot();
          if (imageSrc) {
            framesSent++;
            if (framesSent % 30 === 0) { // Log every 30 frames (3 seconds)
              console.log("📹 [FRAME CAPTURE] Frames sent:", framesSent);
            }
            sendFrame(imageSrc, poseName);
          } else {
            console.warn("⚠️ [FRAME CAPTURE] Failed to get screenshot");
          }
        }, 100);
      }, 500);

      return () => {
        console.log("📹 [FRAME CAPTURE] Cleanup - stopping frame capture");
        clearTimeout(startDelay);
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
        }
      };
    } else {
      console.log("📹 [FRAME CAPTURE] Conditions not met, not starting capture");
    }
  }, [isRealtimeMode, useWebcam, webcamReady, sendFrame, poseName]);

  // Start real-time analysis
  const handleStartRealtime = useCallback(() => {
    console.log("🚀 [START REALTIME] Button clicked");
    console.log("🚀 [START REALTIME] Current state:", {
      isConnected,
      useWebcam,
      webcamReady,
      hasWebcamRef: !!webcamRef.current
    });
    
    console.log("🚀 [START REALTIME] Setting states for real-time mode");
    setIsRealtimeMode(true);
    setUseWebcam(true);
    setRealtimeFeedback(null);
    setFrameCount(0);
    
    if (!isConnected) {
      console.log("🚀 [START REALTIME] Not connected yet, will start after connection");
      setPendingStart(true);
      connectWebSocket();
    } else {
      console.log("🚀 [START REALTIME] Already connected, starting analysis immediately");
      startRealtimeAnalysis(poseName);
    }
  }, [isConnected, connectWebSocket, startRealtimeAnalysis, poseName]);

  // Stop real-time analysis
  const handleStopRealtime = useCallback(() => {
    console.log("🛑 [STOP REALTIME] Button clicked");
    console.log("🛑 [STOP REALTIME] Clearing states and stopping analysis");
    
    setIsRealtimeMode(false);
    setUseWebcam(false);
    setIsAnalyzing(false);
    setWebcamReady(false); // Reset webcam ready state
    setPendingStart(false); // Clear pending start
    stopRealtimeAnalysis();
    
    if (frameIntervalRef.current) {
      console.log("🛑 [STOP REALTIME] Clearing frame interval");
      clearInterval(frameIntervalRef.current);
    }
  }, [stopRealtimeAnalysis]);

  // Capture single photo from webcam
  const capturePhoto = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      console.log("📸 Photo captured");

      // Convert base64 to blob
      fetch(imageSrc)
        .then((res) => res.blob())
        .then((blob) => {
          setCapturedImage(blob);
          analyzeImage(blob);
          setUseWebcam(false);
        });
    }
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      console.log("📁 File selected:", file.name);
      setCapturedImage(file);
      analyzeImage(file);
    }
  }, []);

  // Analyze captured/uploaded image (REST API)
  const analyzeImage = async (imageBlob) => {
    setIsAnalyzing(true);
    console.log("🔍 Analyzing pose:", poseName);

    try {
      const result = await analyzePose(imageBlob, poseName);
      setAnalysisResult(result);
      console.log("✅ Analysis complete:", result);
    } catch (err) {
      console.error("❌ Analysis failed:", err);
      alert("Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Reset and try again
  const handleRetry = () => {
    setCapturedImage(null);
    setAnalysisResult(null);
    setRealtimeFeedback(null);
    setIsAnalyzing(false);
    setIsRealtimeMode(false);
    setFrameCount(0);
  };

  // Safe display of pose name
  const displayPoseName = poseName
    ? poseName.replace(/_/g, " ")
    : "Unknown Pose";

  // Safe benefits handling
  const getBenefits = () => {
    if (!poseDetails?.benefits) return [];
    if (Array.isArray(poseDetails.benefits)) return poseDetails.benefits;
    if (typeof poseDetails.benefits === "string") {
      return poseDetails.benefits
        .split(/[,;•\n]/)
        .map((b) => b.trim())
        .filter((b) => b.length > 0);
    }
    return [];
  };

  const benefits = getBenefits();

  // Use real-time feedback if available, otherwise use REST analysis result
  const currentFeedback = isRealtimeMode
    ? realtimeFeedback
    : analysisResult?.validation;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`fixed inset-0 z-[10000] flex items-center justify-center p-4 ${
        darkMode ? "bg-black/80" : "bg-black/70"
      }`}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className={`relative w-full max-w-6xl max-h-[90vh] rounded-3xl overflow-hidden shadow-2xl ${
          darkMode
            ? "bg-gradient-to-br from-dark-surface to-dark-elev border border-dark-border"
            : "bg-gradient-to-br from-white to-blue-50 border border-white/20"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className={`absolute top-4 right-4 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-110 ${
            darkMode
              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
              : "bg-white/80 hover:bg-white text-gray-700"
          }`}
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

        <div className="overflow-y-auto h-full no-scrollbar">
          <div className="p-6 sm:p-8">
           { /* Header */}
                  <div className="mb-6 pr-12">
                    <div className="flex items-center justify-between mb-2">
                    <h2
                      className={`text-sm uppercase tracking-wider ${
                      darkMode ? "text-emerald-400" : "text-emerald-600"
                      }`}
                    >
                      🧘 Yoga Practice
                    </h2>
                    {isRealtimeMode && (
                      <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                      <span
                        className={`text-xs font-medium ${
                        darkMode ? "text-red-400" : "text-red-600"
                        }`}
                      >
                        LIVE • Frame {frameCount}
                      </span>
                      </div>
                    )}
                    </div>
                    <h1
                    className={`text-2xl sm:text-3xl font-bold capitalize ${
                      darkMode ? "text-white" : "text-gray-900"
                    }`}
                    >
                    {displayPoseName}
                    </h1>
                    {poseDetails?.difficulty && (
                    <span
                      className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${
                      darkMode
                        ? "bg-dark-elev text-emerald-400"
                        : "bg-emerald-100 text-emerald-700"
                      }`}
                    >
                      {poseDetails.difficulty.toUpperCase()}
                    </span>
                    )}
                  </div>

                  {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Camera/Upload Section */}
              <div className="space-y-4">
                {/* Camera/Upload Area */}
                <div
                  className={`relative aspect-video rounded-2xl overflow-hidden ${
                    darkMode
                      ? "bg-dark-elev border border-dark-border"
                      : "bg-gray-100 border border-gray-200"
                  }`}
                >
                  {useWebcam && !capturedImage ? (
                    <>
                      <Webcam
                        ref={webcamRef}
                        audio={false}
                        screenshotFormat="image/jpeg"
                        videoConstraints={{
                          width: 1280,
                          height: 720,
                          facingMode: "user",
                        }}
                        mirrored={true}
                        className="w-full h-full object-cover"
                        onUserMedia={() => {
                          console.log("📹 [WEBCAM] onUserMedia - Webcam is ready!");
                          setWebcamReady(true);
                        }}
                        onUserMediaError={(error) => {
                          console.error("❌ [WEBCAM] onUserMediaError:", error);
                          setWebcamReady(false);
                        }}
                      />
                      {/* Real-time overlay indicators */}
                      {isRealtimeMode && landmarks.length > 0 && (
                        <div className="absolute inset-0 pointer-events-none">
                          {/* You can add pose landmark visualizations here */}
                          <div className="absolute bottom-4 left-4 right-4">
                            <div
                              className={`px-3 py-2 rounded-lg backdrop-blur-md ${
                                darkMode
                                  ? "bg-black/60 text-white"
                                  : "bg-white/60 text-gray-900"
                              }`}
                            >
                              <div className="flex items-center justify-between text-xs">
                                <span>Landmarks: {landmarks.length}</span>
                                <span>
                                  {currentFeedback?.accuracy
                                    ? `${Math.round(currentFeedback.accuracy)}%`
                                    : "Analyzing..."}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  ) : capturedImage ? (
                    <img
                      src={URL.createObjectURL(capturedImage)}
                      alt="Captured pose"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center space-y-4">
                        <span className="text-6xl">📸</span>
                        <p
                          className={`text-sm ${
                            darkMode ? "text-dark-muted" : "text-gray-600"
                          }`}
                        >
                          Choose your practice mode
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Controls */}
                <div className="space-y-3">
                  {!useWebcam && !capturedImage && (
                    <>
                      {/* Real-time Mode Button */}
                      <button
                        onClick={handleStartRealtime}
                        disabled={isLoading}
                        className="w-full px-4 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <span>🔴</span>
                        <span>Real-Time Analysis (Live)</span>
                      </button>

                      {/* Single Photo Mode */}
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => {
                            console.log("📸 [BUTTON] Take Photo clicked");
                            setUseWebcam(true);
                            setWebcamReady(false); // Reset ready state when opening webcam
                          }}
                          disabled={isLoading}
                          className={`px-4 py-3 rounded-xl font-medium transition-all ${
                            darkMode
                              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                              : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                          } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                          📹 Take Photo
                        </button>
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          disabled={isLoading}
                          className={`px-4 py-3 rounded-xl font-medium transition-all ${
                            darkMode
                              ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                              : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                          } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                          📁 Upload
                        </button>
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </>
                  )}

                  {useWebcam && !capturedImage && !isRealtimeMode && (
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        onClick={capturePhoto}
                        className="px-4 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg"
                      >
                        📸 Capture
                      </button>
                      <button
                        onClick={() => {
                          console.log("✕ [BUTTON] Cancel clicked, closing webcam");
                          setUseWebcam(false);
                          setWebcamReady(false);
                        }}
                        className={`px-4 py-3 rounded-xl font-medium transition-all ${
                          darkMode
                            ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                            : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                        }`}
                      >
                        ✕ Cancel
                      </button>
                    </div>
                  )}

                  {isRealtimeMode && (
                    <button
                      onClick={handleStopRealtime}
                      className="w-full px-4 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg"
                    >
                      ⏹️ Stop Real-Time Analysis
                    </button>
                  )}

                  {capturedImage && (
                    <button
                      onClick={handleRetry}
                      className={`w-full px-4 py-3 rounded-xl font-medium transition-all ${
                        darkMode
                          ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                          : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                      }`}
                    >
                      🔄 Try Again
                    </button>
                  )}
                </div>

                {/* Connection Status */}
                {isRealtimeMode && (
                  <div
                    className={`p-3 rounded-lg text-center text-xs ${
                      isConnected
                        ? darkMode
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-emerald-100 text-emerald-700"
                        : darkMode
                        ? "bg-red-500/10 text-red-400"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {isConnected
                      ? "✅ Connected to WebSocket"
                      : "⚠️ Connecting..."}
                  </div>
                )}

                {/* Pose Information */}
                <div
                  className={`p-6 rounded-2xl ${
                    darkMode
                      ? "bg-dark-elev border border-dark-border"
                      : "bg-white border border-gray-200"
                  }`}
                >
                  <h3
                    className={`text-lg font-bold mb-4 ${
                      darkMode ? "text-white" : "text-gray-900"
                    }`}
                  >
                    ℹ️ About This Pose
                  </h3>

                  {poseDetails?.description && (
                    <p
                      className={`text-sm mb-4 ${
                        darkMode ? "text-dark-muted" : "text-gray-600"
                      }`}
                    >
                      {poseDetails.description}
                    </p>
                  )}

                  {benefits.length > 0 && (
                    <div>
                      <p
                        className={`text-sm font-semibold mb-2 ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                      >
                        💪 Benefits:
                      </p>
                      <ul className="text-sm space-y-1">
                        {benefits.map((benefit, idx) => (
                          <li
                            key={idx}
                            className={
                              darkMode ? "text-dark-muted" : "text-gray-600"
                            }
                          >
                            • {benefit}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Analysis Results */}
              <div className="space-y-4">
                {isAnalyzing && !isRealtimeMode ? (
                  <div
                    className={`p-8 rounded-2xl text-center ${
                      darkMode
                        ? "bg-dark-elev border border-dark-border"
                        : "bg-white border border-gray-200"
                    }`}
                  >
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-500 mx-auto mb-4" />
                    <p
                      className={`text-sm ${
                        darkMode ? "text-dark-muted" : "text-gray-600"
                      }`}
                    >
                      Analyzing your pose with AI...
                    </p>
                  </div>
                ) : currentFeedback ? (
                  <>
                    {/* Accuracy Score */}
                    <div
                      className={`p-6 rounded-2xl ${
                        darkMode
                          ? "bg-dark-elev border border-dark-border"
                          : "bg-white border border-gray-200"
                      }`}
                    >
                      <h3
                        className={`text-lg font-bold mb-4 ${
                          darkMode ? "text-white" : "text-gray-900"
                        }`}
                      >
                        📊 Accuracy Score
                      </h3>
                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex-1">
                          <div
                            className={`h-4 rounded-full overflow-hidden ${
                              darkMode ? "bg-dark-surface" : "bg-gray-200"
                            }`}
                          >
                            <motion.div
                              className={`h-full transition-all duration-300 ${
                                currentFeedback.accuracy >= 80
                                  ? "bg-gradient-to-r from-emerald-500 to-emerald-600"
                                  : currentFeedback.accuracy >= 60
                                  ? "bg-gradient-to-r from-yellow-500 to-orange-600"
                                  : "bg-gradient-to-r from-red-500 to-red-600"
                              }`}
                              initial={{ width: 0 }}
                              animate={{
                                width: `${currentFeedback.accuracy || 0}%`,
                              }}
                            />
                          </div>
                        </div>
                        <span
                          className={`text-3xl font-bold ${
                            darkMode ? "text-white" : "text-gray-900"
                          }`}
                        >
                          {Math.round(currentFeedback.accuracy || 0)}%
                        </span>
                      </div>
                      <p
                        className={`text-xs ${
                          darkMode ? "text-dark-muted" : "text-gray-500"
                        }`}
                      >
                        {currentFeedback.accuracy >= 80
                          ? "Excellent form! 🌟"
                          : currentFeedback.accuracy >= 60
                          ? "Good effort! Keep practicing 💪"
                          : "Needs improvement - check feedback below 📝"}
                      </p>
                    </div>

                    {/* Detected Angles (only for REST analysis with full data) */}
                    {analysisResult?.detected_angles && !isRealtimeMode && (
                      <div
                        className={`p-6 rounded-2xl ${
                          darkMode
                            ? "bg-dark-elev border border-dark-border"
                            : "bg-white border border-gray-200"
                        }`}
                      >
                        <h3
                          className={`text-lg font-bold mb-4 ${
                            darkMode ? "text-white" : "text-gray-900"
                          }`}
                        >
                          📐 Detected Angles
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(analysisResult.detected_angles).map(
                            ([joint, angle]) => (
                              <div
                                key={joint}
                                className={`p-3 rounded-lg ${
                                  darkMode ? "bg-dark-surface" : "bg-gray-50"
                                }`}
                              >
                                <p
                                  className={`text-xs font-medium mb-1 capitalize ${
                                    darkMode ? "text-white" : "text-gray-900"
                                  }`}
                                >
                                  {joint.replace(/_/g, " ")}
                                </p>
                                <p
                                  className={`text-lg font-bold ${
                                    darkMode
                                      ? "text-emerald-400"
                                      : "text-emerald-600"
                                  }`}
                                >
                                  {Math.round(angle)}°
                                </p>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                    {/* Feedback */}
                    {currentFeedback.feedback?.length > 0 && (
                      <div
                        className={`p-6 rounded-2xl ${
                          darkMode
                            ? "bg-dark-elev border border-dark-border"
                            : "bg-white border border-gray-200"
                        }`}
                      >
                        <h3
                          className={`text-lg font-bold mb-4 ${
                            darkMode ? "text-white" : "text-gray-900"
                          }`}
                        >
                          💡 Corrections
                        </h3>
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                          {currentFeedback.feedback.map((item, idx) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: idx * 0.1 }}
                              className={`p-4 rounded-lg border-l-4 ${
                                darkMode
                                  ? "bg-dark-surface border-orange-500"
                                  : "bg-orange-50 border-orange-500"
                              }`}
                            >
                              <p
                                className={`text-sm font-medium mb-1 ${
                                  darkMode ? "text-white" : "text-gray-900"
                                }`}
                              >
                                {item.joint}
                              </p>
                              {item.expected > 0 && (
                                <p
                                  className={`text-xs mb-2 ${
                                    darkMode
                                      ? "text-dark-muted"
                                      : "text-gray-600"
                                  }`}
                                >
                                  Expected: {Math.round(item.expected)}° |
                                  Detected: {Math.round(item.detected)}°
                                </p>
                              )}
                              <p
                                className={`text-xs ${
                                  darkMode
                                    ? "text-orange-400"
                                    : "text-orange-700"
                                }`}
                              >
                                {item.correction}
                              </p>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Success Message */}
                    {currentFeedback.valid && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center"
                      >
                        <motion.span
                          animate={{ rotate: [0, 10, -10, 0] }}
                          transition={{ duration: 0.5, repeat: Infinity }}
                          className="text-5xl mb-3 block"
                        >
                          🎉
                        </motion.span>
                        <p
                          className={`font-semibold mb-1 ${
                            darkMode ? "text-emerald-400" : "text-emerald-600"
                          }`}
                        >
                          Perfect Pose!
                        </p>
                        <p className="text-sm text-emerald-600 dark:text-emerald-400">
                          You've mastered this asana! 🧘‍♀️
                        </p>
                      </motion.div>
                    )}
                  </>
                ) : (
                  <div
                    className={`p-8 rounded-2xl text-center ${
                      darkMode
                        ? "bg-dark-elev border border-dark-border"
                        : "bg-white border border-gray-200"
                    }`}
                  >
                    <span className="text-6xl mb-4 block">🧘</span>
                    <h3
                      className={`text-lg font-bold mb-2 ${
                        darkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      Ready to Practice?
                    </h3>
                    <p
                      className={`text-sm mb-4 ${
                        darkMode ? "text-dark-muted" : "text-gray-600"
                      }`}
                    >
                      Choose your practice mode:
                    </p>
                    <div className="space-y-2 text-left">
                      <div
                        className={`p-3 rounded-lg ${
                          darkMode ? "bg-dark-surface" : "bg-gray-50"
                        }`}
                      >
                        <p
                          className={`text-xs font-semibold mb-1 ${
                            darkMode ? "text-red-400" : "text-red-600"
                          }`}
                        >
                          🔴 Real-Time Mode
                        </p>
                        <p
                          className={`text-xs ${
                            darkMode ? "text-dark-muted" : "text-gray-600"
                          }`}
                        >
                          Live feedback as you practice (WebSocket)
                        </p>
                      </div>
                      <div
                        className={`p-3 rounded-lg ${
                          darkMode ? "bg-dark-surface" : "bg-gray-50"
                        }`}
                      >
                        <p
                          className={`text-xs font-semibold mb-1 ${
                            darkMode ? "text-emerald-400" : "text-emerald-600"
                          }`}
                        >
                          📸 Single Photo Mode
                        </p>
                        <p
                          className={`text-xs ${
                            darkMode ? "text-dark-muted" : "text-gray-600"
                          }`}
                        >
                          Capture or upload for detailed analysis
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default YogaPractice;
