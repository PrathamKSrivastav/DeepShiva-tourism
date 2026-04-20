import React, { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Webcam from "react-webcam";
import { useYoga } from "../hooks/useYoga";

// MediaPipe Pose is loaded from CDN to avoid Vite/WASM bundling issues.
// The library attaches itself to window.Pose after the script loads.
// IMPORTANT: pin the version — `@latest` on jsDelivr has shipped builds with
// a bug in pose_solution_packed_assets_loader.js that throws
// "Cannot read properties of undefined" on xhr.onprogress and breaks model load.
const MEDIAPIPE_POSE_VERSION = "0.5.1675469404";
const MEDIAPIPE_POSE_CDN = `https://cdn.jsdelivr.net/npm/@mediapipe/pose@${MEDIAPIPE_POSE_VERSION}/pose.js`;

function useBrowserPose(onResults) {
  const poseRef = useRef(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      // Inject CDN script if not already present
      if (!document.getElementById("mediapipe-pose-script")) {
        await new Promise((resolve, reject) => {
          const script = document.createElement("script");
          script.id = "mediapipe-pose-script";
          script.src = MEDIAPIPE_POSE_CDN;
          script.crossOrigin = "anonymous";
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
      }

      if (!mounted) return;

      const { Pose } = window;
      if (!Pose) return;

      const pose = new Pose({
        locateFile: (file) =>
          `https://cdn.jsdelivr.net/npm/@mediapipe/pose@${MEDIAPIPE_POSE_VERSION}/${file}`,
      });

      pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      pose.onResults((results) => {
        if (results.poseLandmarks) {
          onResults(results.poseLandmarks);
        }
      });

      poseRef.current = pose;
      if (mounted) setReady(true);
    };

    init().catch((e) => console.error("MediaPipe Pose init failed:", e));

    return () => {
      mounted = false;
      poseRef.current?.close?.();
    };
  }, [onResults]);

  return { pose: poseRef, ready };
}

const YogaPractice = ({ poseName, poseDetails, onClose, darkMode }) => {
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [useWebcam, setUseWebcam] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isRealtimeMode, setIsRealtimeMode] = useState(false);
  const [realtimeFeedback, setRealtimeFeedback] = useState(null);
  const [frameCount, setFrameCount] = useState(0);
  const [webcamReady, setWebcamReady] = useState(false);
  const [pendingStart, setPendingStart] = useState(false);

  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const offscreenCanvasRef = useRef(null);

  const {
    analyzeLandmarks,
    connectWebSocket,
    disconnectWebSocket,
    onWebSocketMessage,
    startRealtimeAnalysis,
    stopRealtimeAnalysis,
    sendLandmarks,
    isConnected,
    isLoading,
    error,
  } = useYoga();

  // ── landmark callback (stable reference so useBrowserPose doesn't re-init)
  const lastLandmarksRef = useRef(null);
  const handlePoseResults = useCallback((landmarks) => {
    // Normalise to plain objects for JSON serialisation
    lastLandmarksRef.current = landmarks.map((lm) => ({
      x: lm.x,
      y: lm.y,
      z: lm.z ?? 0,
      visibility: lm.visibility ?? 1,
    }));
  }, []);

  const { pose: poseRef, ready: poseReady } = useBrowserPose(handlePoseResults);

  // ── feed webcam frames into MediaPipe
  const sendFrameToMediaPipe = useCallback(async () => {
    if (!poseRef.current || !webcamRef.current) return;
    const video = webcamRef.current.video;
    if (!video || video.readyState < 2) return;

    // Draw video frame onto offscreen canvas for MediaPipe
    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement("canvas");
    }
    const canvas = offscreenCanvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    await poseRef.current.send({ image: canvas });
  }, [poseRef]);

  // ── auto-start analysis once WS connects
  useEffect(() => {
    if (isConnected && pendingStart && isRealtimeMode) {
      setPendingStart(false);
      startRealtimeAnalysis(poseName);
    }
  }, [isConnected, pendingStart, isRealtimeMode, poseName, startRealtimeAnalysis]);

  // ── WS message listeners
  useEffect(() => {
    const unsubs = [
      onWebSocketMessage("analysis_started", () => setIsAnalyzing(true)),
      onWebSocketMessage("feedback", (data) => {
        setRealtimeFeedback(data.data);
        setFrameCount((n) => n + 1);
      }),
      onWebSocketMessage("analysis_stopped", () => setIsAnalyzing(false)),
      onWebSocketMessage("error", (data) => console.error("WS error:", data.message)),
    ];
    return () => unsubs.forEach((u) => u());
  }, [onWebSocketMessage]);

  // ── realtime frame loop: run MediaPipe → send landmarks to backend
  useEffect(() => {
    if (!isRealtimeMode || !useWebcam || !webcamReady || !poseReady) return;

    const delay = setTimeout(() => {
      frameIntervalRef.current = setInterval(async () => {
        await sendFrameToMediaPipe();
        if (lastLandmarksRef.current) {
          sendLandmarks(lastLandmarksRef.current, poseName);
        }
      }, 100); // 10 FPS
    }, 500);

    return () => {
      clearTimeout(delay);
      clearInterval(frameIntervalRef.current);
    };
  }, [isRealtimeMode, useWebcam, webcamReady, poseReady, sendFrameToMediaPipe, sendLandmarks, poseName]);

  // ── cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(frameIntervalRef.current);
      if (isRealtimeMode) {
        stopRealtimeAnalysis();
        disconnectWebSocket();
      }
    };
  }, []); // eslint-disable-line

  const handleStartRealtime = useCallback(() => {
    setIsRealtimeMode(true);
    setUseWebcam(true);
    setRealtimeFeedback(null);
    setFrameCount(0);
    if (!isConnected) {
      setPendingStart(true);
      connectWebSocket();
    } else {
      startRealtimeAnalysis(poseName);
    }
  }, [isConnected, connectWebSocket, startRealtimeAnalysis, poseName]);

  const handleStopRealtime = useCallback(() => {
    setIsRealtimeMode(false);
    setUseWebcam(false);
    setIsAnalyzing(false);
    setWebcamReady(false);
    setPendingStart(false);
    stopRealtimeAnalysis();
    clearInterval(frameIntervalRef.current);
  }, [stopRealtimeAnalysis]);

  // ── single-photo capture: run MediaPipe once then call REST
  const captureAndAnalyze = useCallback(async () => {
    if (!poseRef.current || !webcamRef.current) return;
    setIsAnalyzing(true);

    try {
      // Capture screenshot for display
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        const res = await fetch(imageSrc);
        setCapturedImage(await res.blob());
      }
      setUseWebcam(false);

      // Run MediaPipe on the current frame
      await sendFrameToMediaPipe();
      await new Promise((r) => setTimeout(r, 100)); // let onResults fire

      if (!lastLandmarksRef.current) {
        alert("No pose detected. Ensure your full body is visible.");
        return;
      }

      const result = await analyzeLandmarks(lastLandmarksRef.current, poseName);
      setAnalysisResult(result);
    } catch (err) {
      console.error("Analysis failed:", err);
      alert("Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }, [poseRef, sendFrameToMediaPipe, analyzeLandmarks, poseName]);

  // ── file upload: draw onto canvas → run MediaPipe → REST
  const handleFileUpload = useCallback(
    async (event) => {
      const file = event.target.files[0];
      if (!file || !poseRef.current) return;
      setIsAnalyzing(true);
      setCapturedImage(file);

      try {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        await new Promise((r) => { img.onload = r; });

        const canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        canvas.getContext("2d").drawImage(img, 0, 0);

        await poseRef.current.send({ image: canvas });
        await new Promise((r) => setTimeout(r, 150));

        if (!lastLandmarksRef.current) {
          alert("No pose detected. Please use a clear full-body photo.");
          return;
        }

        const result = await analyzeLandmarks(lastLandmarksRef.current, poseName);
        setAnalysisResult(result);
      } catch (err) {
        console.error("File analysis failed:", err);
        alert("Analysis failed. Please try again.");
      } finally {
        setIsAnalyzing(false);
      }
    },
    [poseRef, analyzeLandmarks, poseName]
  );

  const handleRetry = () => {
    setCapturedImage(null);
    setAnalysisResult(null);
    setRealtimeFeedback(null);
    setIsAnalyzing(false);
    setIsRealtimeMode(false);
    setFrameCount(0);
    lastLandmarksRef.current = null;
  };

  const displayPoseName = poseName ? poseName.replace(/_/g, " ") : "Unknown Pose";

  const getBenefits = () => {
    if (!poseDetails?.benefits) return [];
    if (Array.isArray(poseDetails.benefits)) return poseDetails.benefits;
    if (typeof poseDetails.benefits === "string") {
      return poseDetails.benefits.split(/[,;•\n]/).map((b) => b.trim()).filter(Boolean);
    }
    return [];
  };

  const benefits = getBenefits();
  const currentFeedback = isRealtimeMode ? realtimeFeedback : analysisResult?.validation;

  // shared class helpers
  const card = `p-6 rounded-2xl ${darkMode ? "bg-dark-elev border border-dark-border" : "bg-white border border-gray-200"}`;
  const muted = darkMode ? "text-dark-muted" : "text-gray-600";
  const heading = `text-lg font-bold mb-4 ${darkMode ? "text-white" : "text-gray-900"}`;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={`fixed inset-0 z-[10000] flex items-center justify-center p-4 ${darkMode ? "bg-black/80" : "bg-black/70"}`}
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
        {/* Close */}
        <button
          onClick={onClose}
          className={`absolute top-4 right-4 z-10 w-10 h-10 rounded-full flex items-center justify-center transition-all hover:scale-110 ${
            darkMode ? "bg-dark-elev hover:bg-dark-elev/80 text-white" : "bg-white/80 hover:bg-white text-gray-700"
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="overflow-y-auto h-full no-scrollbar">
          <div className="p-6 sm:p-8">
            {/* Header */}
            <div className="mb-6 pr-12">
              <div className="flex items-center justify-between mb-2">
                <h2 className={`text-sm uppercase tracking-wider ${darkMode ? "text-emerald-400" : "text-emerald-600"}`}>
                  🧘 Yoga Practice
                </h2>
                {isRealtimeMode && (
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                    <span className={`text-xs font-medium ${darkMode ? "text-red-400" : "text-red-600"}`}>
                      LIVE • Frame {frameCount}
                    </span>
                  </div>
                )}
              </div>
              <h1 className={`text-2xl sm:text-3xl font-bold capitalize ${darkMode ? "text-white" : "text-gray-900"}`}>
                {displayPoseName}
              </h1>
              {poseDetails?.difficulty && (
                <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${
                  darkMode ? "bg-dark-elev text-emerald-400" : "bg-emerald-100 text-emerald-700"
                }`}>
                  {poseDetails.difficulty.toUpperCase()}
                </span>
              )}

              {/* MediaPipe loading indicator */}
              {!poseReady && (
                <div className={`mt-2 text-xs ${muted}`}>
                  ⏳ Loading pose detection model…
                </div>
              )}
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left: Camera/Upload */}
              <div className="space-y-4">
                <div className={`relative aspect-video rounded-2xl overflow-hidden ${
                  darkMode ? "bg-dark-elev border border-dark-border" : "bg-gray-100 border border-gray-200"
                }`}>
                  {useWebcam && !capturedImage ? (
                    <Webcam
                      ref={webcamRef}
                      audio={false}
                      screenshotFormat="image/jpeg"
                      videoConstraints={{ width: 1280, height: 720, facingMode: "user" }}
                      mirrored
                      className="w-full h-full object-cover"
                      onUserMedia={() => setWebcamReady(true)}
                      onUserMediaError={() => setWebcamReady(false)}
                    />
                  ) : capturedImage ? (
                    <img src={URL.createObjectURL(capturedImage)} alt="Captured pose" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center space-y-4">
                        <span className="text-6xl">📸</span>
                        <p className={`text-sm ${muted}`}>Choose your practice mode</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Controls */}
                <div className="space-y-3">
                  {!useWebcam && !capturedImage && (
                    <>
                      <button
                        onClick={handleStartRealtime}
                        disabled={isLoading || !poseReady}
                        className="w-full px-4 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <span>🔴</span>
                        <span>{poseReady ? "Real-Time Analysis (Live)" : "Loading model…"}</span>
                      </button>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => { setUseWebcam(true); setWebcamReady(false); }}
                          disabled={isLoading || !poseReady}
                          className={`px-4 py-3 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                            darkMode ? "bg-dark-elev hover:bg-dark-elev/80 text-white" : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                          }`}
                        >
                          Take Photo
                        </button>
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          disabled={isLoading || !poseReady}
                          className={`px-4 py-3 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                            darkMode ? "bg-dark-elev hover:bg-dark-elev/80 text-white" : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                          }`}
                        >
                          Upload
                        </button>
                      </div>
                      <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
                    </>
                  )}

                  {useWebcam && !capturedImage && !isRealtimeMode && (
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        onClick={captureAndAnalyze}
                        disabled={!webcamReady || !poseReady}
                        className="px-4 py-3 rounded-xl font-medium transition-all bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg disabled:opacity-50"
                      >
                        Capture
                      </button>
                      <button
                        onClick={() => { setUseWebcam(false); setWebcamReady(false); }}
                        className={`px-4 py-3 rounded-xl font-medium transition-all ${
                          darkMode ? "bg-dark-elev hover:bg-dark-elev/80 text-white" : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
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
                      ⏹️ Stop
                    </button>
                  )}

                  {capturedImage && (
                    <button
                      onClick={handleRetry}
                      className={`w-full px-4 py-3 rounded-xl font-medium transition-all ${
                        darkMode ? "bg-dark-elev hover:bg-dark-elev/80 text-white" : "bg-white hover:bg-gray-50 text-gray-700 border border-gray-200"
                      }`}
                    >
                      🔄 Try Again
                    </button>
                  )}
                </div>

                {isRealtimeMode && (
                  <div className={`p-3 rounded-lg text-center text-xs ${
                    isConnected
                      ? darkMode ? "bg-emerald-500/10 text-emerald-400" : "bg-emerald-100 text-emerald-700"
                      : darkMode ? "bg-red-500/10 text-red-400" : "bg-red-100 text-red-700"
                  }`}>
                    {isConnected ? "Connected" : "Connecting…"}
                  </div>
                )}

                {/* About pose */}
                <div className={card}>
                  <h3 className={heading}>ℹ️ About This Pose</h3>
                  {poseDetails?.description && <p className={`text-sm mb-4 ${muted}`}>{poseDetails.description}</p>}
                  {benefits.length > 0 && (
                    <>
                      <p className={`text-sm font-semibold mb-2 ${darkMode ? "text-white" : "text-gray-900"}`}>💪 Benefits:</p>
                      <ul className="text-sm space-y-1">
                        {benefits.map((b, i) => (
                          <li key={i} className={muted}>• {b}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              </div>

              {/* Right: Results */}
              <div className="space-y-4">
                {isAnalyzing && !isRealtimeMode ? (
                  <div className={`p-8 rounded-2xl text-center ${darkMode ? "bg-dark-elev border border-dark-border" : "bg-white border border-gray-200"}`}>
                    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-500 mx-auto mb-4" />
                    <p className={`text-sm ${muted}`}>Analysing your pose…</p>
                  </div>
                ) : currentFeedback ? (
                  <>
                    {/* Accuracy */}
                    <div className={card}>
                      <h3 className={heading}>🎯 Accuracy Score</h3>
                      <div className="flex items-center gap-4 mb-3">
                        <div className="flex-1">
                          <div className={`h-4 rounded-full overflow-hidden ${darkMode ? "bg-dark-surface" : "bg-gray-200"}`}>
                            <motion.div
                              className={`h-full ${
                                currentFeedback.accuracy >= 80
                                  ? "bg-gradient-to-r from-emerald-500 to-emerald-600"
                                  : currentFeedback.accuracy >= 60
                                  ? "bg-gradient-to-r from-yellow-500 to-orange-600"
                                  : "bg-gradient-to-r from-red-500 to-red-600"
                              }`}
                              initial={{ width: 0 }}
                              animate={{ width: `${currentFeedback.accuracy || 0}%` }}
                            />
                          </div>
                        </div>
                        <span className={`text-3xl font-bold ${darkMode ? "text-white" : "text-gray-900"}`}>
                          {Math.round(currentFeedback.accuracy || 0)}%
                        </span>
                      </div>
                      <p className={`text-xs ${muted}`}>
                        {currentFeedback.accuracy >= 80
                          ? "Excellent form! 🌟"
                          : currentFeedback.accuracy >= 60
                          ? "Good effort! Keep practising 💪"
                          : "Needs improvement — check feedback below"}
                      </p>
                    </div>

                    {/* Detected angles (REST only) */}
                    {analysisResult?.detected_angles && !isRealtimeMode && (
                      <div className={card}>
                        <h3 className={heading}>📐 Detected Angles</h3>
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(analysisResult.detected_angles).map(([joint, angle]) => (
                            <div key={joint} className={`p-3 rounded-lg ${darkMode ? "bg-dark-surface" : "bg-gray-50"}`}>
                              <p className={`text-xs font-medium mb-1 capitalize ${darkMode ? "text-white" : "text-gray-900"}`}>
                                {joint.replace(/_/g, " ")}
                              </p>
                              <p className={`text-lg font-bold ${darkMode ? "text-emerald-400" : "text-emerald-600"}`}>
                                {Math.round(angle)}°
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Feedback */}
                    {currentFeedback.feedback?.length > 0 && (
                      <div className={card}>
                        <h3 className={heading}>💡 Corrections</h3>
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                          {currentFeedback.feedback.map((item, i) => (
                            <motion.div
                              key={i}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: i * 0.05 }}
                              className={`p-4 rounded-lg border-l-4 ${darkMode ? "bg-dark-surface border-orange-500" : "bg-orange-50 border-orange-500"}`}
                            >
                              <p className={`text-sm font-medium mb-1 ${darkMode ? "text-white" : "text-gray-900"}`}>{item.joint}</p>
                              {item.expected > 0 && (
                                <p className={`text-xs mb-1 ${muted}`}>
                                  Expected: {Math.round(item.expected)}° | Detected: {Math.round(item.detected)}°
                                </p>
                              )}
                              <p className={`text-xs ${darkMode ? "text-orange-400" : "text-orange-700"}`}>{item.correction}</p>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}

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
                        >🎉</motion.span>
                        <p className={`font-semibold mb-1 ${darkMode ? "text-emerald-400" : "text-emerald-600"}`}>Perfect Pose!</p>
                        <p className="text-sm text-emerald-600">You've mastered this asana! 🧘‍♀️</p>
                      </motion.div>
                    )}
                  </>
                ) : (
                  <div className={`p-8 rounded-2xl text-center ${darkMode ? "bg-dark-elev border border-dark-border" : "bg-white border border-gray-200"}`}>
                    <span className="text-6xl mb-4 block">🧘</span>
                    <h3 className={`text-lg font-bold mb-2 ${darkMode ? "text-white" : "text-gray-900"}`}>Ready to Practice?</h3>
                    <p className={`text-sm mb-4 ${muted}`}>Choose your practice mode:</p>
                    <div className="space-y-2 text-left">
                      <div className={`p-3 rounded-lg ${darkMode ? "bg-dark-surface" : "bg-gray-50"}`}>
                        <p className={`text-xs font-semibold mb-1 ${darkMode ? "text-red-400" : "text-red-600"}`}>🔴 Real-Time Mode</p>
                        <p className={`text-xs ${muted}`}>Live feedback as you practise</p>
                      </div>
                      <div className={`p-3 rounded-lg ${darkMode ? "bg-dark-surface" : "bg-gray-50"}`}>
                        <p className={`text-xs font-semibold mb-1 ${darkMode ? "text-emerald-400" : "text-emerald-600"}`}>Single Photo Mode</p>
                        <p className={`text-xs ${muted}`}>Capture or upload for detailed analysis</p>
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
