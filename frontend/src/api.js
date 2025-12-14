import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    // Use new key name
    const token = localStorage.getItem("app_session_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("🔐 Request with token:", config.url);
    } else {
      console.log("📭 Request without token:", config.url);
    }
    return config;
  },
  (error) => {
    console.error("❌ Request error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("auth_token");
      // Optionally redirect to login or refresh page
      // window.location.reload()
    }
    return Promise.reject(error);
  }
);

// ============= AUTH APIs =============

export const loginWithGoogle = async (credential) => {
  try {
    console.log("🔐 API: Logging in with Google...");
    console.log("📤 Sending credential to backend...");

    const response = await apiClient.post("/auth/google", { credential });

    console.log("📥 Backend response:", response);
    console.log("📥 Response data:", response.data);
    console.log("📥 Access token exists:", !!response.data.access_token);
    console.log("📥 Access token:", response.data.access_token);

    // Check for weird characters
    const token = response.data.access_token;
    if (token) {
      console.log("🔍 Token contains newline:", token.includes("\n"));
      console.log("🔍 Token contains tab:", token.includes("\t"));
      console.log("🔍 Token contains space:", token.includes(" "));
      console.log("🔍 Token length:", token.length);
      console.log("🔍 Token charCode[0]:", token.charCodeAt(0));
    }

    console.log("✅ Login API successful:", response.data.user.email);
    return response.data;
  } catch (error) {
    console.error("❌ API Login error:", error);
    throw error;
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await apiClient.get("/auth/me");
    return response.data;
  } catch (error) {
    console.error("Error getting current user:", error);
    throw error;
  }
};

export const logout = async () => {
  try {
    const response = await apiClient.post("/auth/logout");
    return response.data;
  } catch (error) {
    console.error("Error logging out:", error);
    throw error;
  }
};

export const verifyToken = async () => {
  try {
    console.log("🔍 Verifying token...");
    const token = localStorage.getItem("app_session_token");
    console.log("🎫 Token exists:", !!token);

    const response = await apiClient.get("/auth/verify");
    console.log("✅ Token verification result:", response.data.valid);
    return response.data;
  } catch (error) {
    console.error("❌ Token verification error:", error);
    return { valid: false, user: null };
  }
};

// ============= CHAT APIs =============

export const fetchPersonas = async () => {
  try {
    const response = await apiClient.get("/personas");
    return response.data;
  } catch (error) {
    console.error("Error fetching personas:", error);
    throw error;
  }
};

// Update sendChatMessage to include session_id
export const sendChatMessage = async (
  message,
  persona,
  context = {},
  sessionId = null
) => {
  try {
    const response = await apiClient.post("/chat", {
      message,
      persona,
      context,
      session_id: sessionId, // ADD THIS
    });
    return response.data;
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
};

export const getChatHistory = async (persona = null, limit = 50) => {
  try {
    const params = { limit };
    if (persona) params.persona = persona;
    const response = await apiClient.get("/chat/sessions", { params }); // Changed from /chat/history
    return response.data;
  } catch (error) {
    console.error("Error fetching chat history:", error);
    throw error;
  }
};

export const deleteChat = async (chatId) => {
  try {
    const response = await apiClient.delete(`/chat/sessions/${chatId}`); // Changed from /chat/history
    return response.data;
  } catch (error) {
    console.error("Error deleting chat:", error);
    throw error;
  }
};

// ============= CHAT SESSION APIs (NEW) =============

export const createNewChatSession = async (persona, title = null) => {
  try {
    const response = await apiClient.post("/chat/sessions/new", {
      persona,
      title,
    });
    return response.data;
  } catch (error) {
    console.error("Error creating session:", error);
    throw error;
  }
};

export const getAllChatSessions = async (persona = null, limit = 50) => {
  try {
    const params = { limit };
    if (persona) params.persona = persona;
    const response = await apiClient.get("/chat/sessions", { params });
    return response.data;
  } catch (error) {
    console.error("Error getting sessions:", error);
    throw error;
  }
};

export const getChatSession = async (sessionId) => {
  try {
    const response = await apiClient.get(`/chat/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error("Error getting session:", error);
    throw error;
  }
};

export const updateSessionTitle = async (sessionId, title) => {
  try {
    const response = await apiClient.put(`/chat/sessions/${sessionId}/title`, {
      title,
    });
    return response.data;
  } catch (error) {
    console.error("Error updating title:", error);
    throw error;
  }
};

export const deleteChatSession = async (sessionId) => {
  try {
    const response = await apiClient.delete(`/chat/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting session:", error);
    throw error;
  }
};

// ============= MOCK DATA APIs =============

export const fetchWeather = async () => {
  try {
    const response = await apiClient.get("/mock/weather");
    return response.data;
  } catch (error) {
    console.error("Error fetching weather:", error);
    throw error;
  }
};

export const fetchCrowd = async () => {
  try {
    const response = await apiClient.get("/mock/crowd");
    return response.data;
  } catch (error) {
    console.error("Error fetching crowd data:", error);
    throw error;
  }
};

export const fetchFestivals = async () => {
  try {
    const response = await apiClient.get("/mock/festivals");
    return response.data;
  } catch (error) {
    console.error("Error fetching festivals:", error);
    throw error;
  }
};

export const fetchEmergency = async () => {
  try {
    const response = await apiClient.get("/mock/emergency");
    return response.data;
  } catch (error) {
    console.error("Error fetching emergency data:", error);
    throw error;
  }
};

export default apiClient;
