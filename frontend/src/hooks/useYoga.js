import { useState, useCallback, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace("http", "ws");

export const useYoga = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [availablePoses, setAvailablePoses] = useState([]);
  const [poseDetails, setPoseDetails] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const listenersRef = useRef({});

  /**
   * Connect to WebSocket for real-time analysis
   */
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("🔌 WebSocket already connected");
      return;
    }

    try {
      console.log("🔌 Connecting to WebSocket:", `${WS_URL}/api/yoga/ws`);
      const ws = new WebSocket(`${WS_URL}/api/yoga/ws`);

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📨 WebSocket message:", data.type);

          const listeners = listenersRef.current[data.type] || [];
          listeners.forEach((listener) => listener(data));
        } catch (err) {
          console.error("❌ Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setError("WebSocket connection error");
      };

      ws.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;

        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("🔄 Attempting to reconnect...");
          connectWebSocket();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("❌ WebSocket connection failed:", err);
      setError(err.message);
    }
  }, []);

  /**
   * Disconnect WebSocket
   */
  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      console.log("🔌 Disconnecting WebSocket");
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Send message to WebSocket
   */
  const sendWebSocketMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } else {
      console.error("❌ WebSocket not connected");
      return false;
    }
  }, []);

  /**
   * Register listener for WebSocket messages
   */
  const onWebSocketMessage = useCallback((messageType, callback) => {
    if (!listenersRef.current[messageType]) {
      listenersRef.current[messageType] = [];
    }
    listenersRef.current[messageType].push(callback);

    return () => {
      listenersRef.current[messageType] = listenersRef.current[
        messageType
      ].filter((cb) => cb !== callback);
    };
  }, []);

  /**
   * Start real-time pose analysis
   */
  const startRealtimeAnalysis = useCallback(
    (poseName) => {
      return sendWebSocketMessage({
        action: "start",
        pose_name: poseName,
      });
    },
    [sendWebSocketMessage]
  );

  /**
   * Stop real-time pose analysis
   */
  const stopRealtimeAnalysis = useCallback(() => {
    return sendWebSocketMessage({
      action: "stop",
    });
  }, [sendWebSocketMessage]);

  /**
   * Send video frame for analysis
   */
  const sendFrame = useCallback(
    (imageBase64, poseName) => {
      return sendWebSocketMessage({
        action: "frame",
        image: imageBase64,
        pose_name: poseName,
      });
    },
    [sendWebSocketMessage]
  );

  /**
   * Get pose information via WebSocket
   */
  const getPoseInfoWS = useCallback(
    (poseName) => {
      return sendWebSocketMessage({
        action: "get_pose_info",
        pose_name: poseName,
      });
    },
    [sendWebSocketMessage]
  );

  /**
   * List all poses via WebSocket
   */
  const listPosesWS = useCallback(() => {
    return sendWebSocketMessage({
      action: "list_poses",
    });
  }, [sendWebSocketMessage]);

  /**
   * Send ping to keep connection alive
   */
  const ping = useCallback(() => {
    return sendWebSocketMessage({
      action: "ping",
    });
  }, [sendWebSocketMessage]);

  /**
   * Fetch all available yoga poses (REST)
   */
  const fetchPoses = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/yoga/poses`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Fetched poses:", data);
      return data.poses;
    } catch (err) {
      console.error("❌ Error fetching poses:", err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch available poses and store in state
   */
  const fetchAvailablePoses = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/yoga/poses`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Fetched available poses:", data);

      // Store full pose objects with image and duration
      setAvailablePoses(data.poses);

      return data.poses;
    } catch (err) {
      console.error("❌ Error fetching available poses:", err);
      setError(err.message);
      setAvailablePoses([]);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Get details for a specific pose (REST)
   */
  const getPoseDetails = useCallback(async (poseName) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/yoga/poses/${poseName}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Fetched pose details:", data);
      return data;
    } catch (err) {
      console.error(`❌ Error fetching pose details for ${poseName}:`, err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch pose details and store in state
   */
  const fetchPoseDetails = useCallback(async (poseName) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/yoga/poses/${poseName}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Fetched and stored pose details:", data);

      setPoseDetails(data);

      return { success: true, details: data };
    } catch (err) {
      console.error(`❌ Error fetching pose details for ${poseName}:`, err);
      setError(err.message);
      setPoseDetails(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Analyze a pose from an image blob (REST)
   */
  const analyzePose = useCallback(async (imageBlob, poseName) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("image", imageBlob, "pose.jpg");
      formData.append("pose_name", poseName);

      const response = await fetch(`${API_URL}/api/yoga/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("✅ Analysis result:", data);
      return data;
    } catch (err) {
      console.error("❌ Error analyzing pose:", err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Analyze a pose from a base64 image (REST)
   */
  const analyzeBase64 = useCallback(async (imageBase64, poseName) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/yoga/analyze-base64`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pose_name: poseName,
          image_base64: imageBase64,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      console.log("✅ Base64 analysis result:", data);
      return data;
    } catch (err) {
      console.error("❌ Error analyzing base64 pose:", err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Check yoga system health (REST)
   */
  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/yoga/health`);
      const data = await response.json();
      console.log("✅ Health check:", data);
      return data;
    } catch (err) {
      console.error("❌ Error checking yoga health:", err);
      return { status: "error", error: err.message };
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    // REST API methods
    fetchPoses,
    getPoseDetails,
    analyzePose,
    analyzeBase64,
    checkHealth,

    // State management methods
    fetchAvailablePoses,
    fetchPoseDetails,

    // WebSocket methods
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
    onWebSocketMessage,
    startRealtimeAnalysis,
    stopRealtimeAnalysis,
    sendFrame,
    getPoseInfoWS,
    listPosesWS,
    ping,

    // State
    isLoading,
    error,
    isConnected,
    availablePoses,
    poseDetails,
  };
};
