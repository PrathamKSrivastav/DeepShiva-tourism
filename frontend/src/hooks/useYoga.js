import { useState, useCallback, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace("https", "wss").replace("http", "ws");

export const useYoga = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [availablePoses, setAvailablePoses] = useState([]);
  const [poseDetails, setPoseDetails] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const listenersRef = useRef({});
  const reconnectRef = useRef(true);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_URL}/api/yoga/ws`);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const listeners = listenersRef.current[data.type] || [];
          listeners.forEach((cb) => cb(data));
        } catch (err) {
          console.error("WS parse error:", err);
        }
      };

      ws.onerror = () => setError("WebSocket connection error");

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        if (reconnectRef.current) {
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const disconnectWebSocket = useCallback(() => {
    reconnectRef.current = false;
    clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendWebSocketMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const onWebSocketMessage = useCallback((messageType, callback) => {
    if (!listenersRef.current[messageType]) {
      listenersRef.current[messageType] = [];
    }
    listenersRef.current[messageType].push(callback);
    return () => {
      listenersRef.current[messageType] = listenersRef.current[messageType].filter(
        (cb) => cb !== callback
      );
    };
  }, []);

  const startRealtimeAnalysis = useCallback(
    (poseName) => sendWebSocketMessage({ action: "start", pose_name: poseName }),
    [sendWebSocketMessage]
  );

  const stopRealtimeAnalysis = useCallback(
    () => sendWebSocketMessage({ action: "stop" }),
    [sendWebSocketMessage]
  );

  /**
   * Send browser-detected landmarks to backend for validation.
   * landmarks: array of 33 {x, y, z, visibility} objects from @mediapipe/pose
   */
  const sendLandmarks = useCallback(
    (landmarks, poseName) =>
      sendWebSocketMessage({ action: "frame", landmarks, pose_name: poseName }),
    [sendWebSocketMessage]
  );

  const fetchPoses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/yoga/poses`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.poses;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchAvailablePoses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/yoga/poses`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAvailablePoses(data.poses);
      return data.poses;
    } catch (err) {
      setError(err.message);
      setAvailablePoses([]);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getPoseDetails = useCallback(async (poseName) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/yoga/poses/${poseName}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchPoseDetails = useCallback(async (poseName) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/yoga/poses/${poseName}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPoseDetails(data);
      return { success: true, details: data };
    } catch (err) {
      setError(err.message);
      setPoseDetails(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Send browser-detected landmarks for single-shot REST analysis.
   * landmarks: array of 33 {x, y, z, visibility} objects
   */
  const analyzeLandmarks = useCallback(async (landmarks, poseName) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/yoga/analyze-landmarks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pose_name: poseName, landmarks }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/yoga/health`);
      return await res.json();
    } catch (err) {
      return { status: "error", error: err.message };
    }
  }, []);

  useEffect(() => {
    reconnectRef.current = true;
    return () => disconnectWebSocket();
  }, [disconnectWebSocket]);

  return {
    fetchPoses,
    fetchAvailablePoses,
    fetchPoseDetails,
    getPoseDetails,
    analyzeLandmarks,
    checkHealth,
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
    onWebSocketMessage,
    startRealtimeAnalysis,
    stopRealtimeAnalysis,
    sendLandmarks,
    isLoading,
    error,
    isConnected,
    availablePoses,
    poseDetails,
  };
};
