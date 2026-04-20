import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import Emergency from "./emergencyPage.jsx";
import App from "./App.jsx";
import LandingPage from "./landingPage/LandingPage.jsx";
import "./index.css";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// @react-oauth/google's <GoogleOAuthProvider> + every <GoogleLogin> each call
// google.accounts.id.initialize() on mount. Re-mounting (route change, StrictMode)
// produces repeated GSI_LOGGER warnings. Make initialize idempotent per clientId.
(function patchGsiInitialize() {
  const waitForGsi = (cb, tries = 40) => {
    if (window.google?.accounts?.id) return cb();
    if (tries <= 0) return;
    setTimeout(() => waitForGsi(cb, tries - 1), 100);
  };
  waitForGsi(() => {
    const id = window.google.accounts.id;
    if (id.__dsPatched) return;
    const original = id.initialize.bind(id);
    let lastKey = null;
    id.initialize = (config) => {
      const key = config?.client_id || config?.clientId || "_";
      if (key === lastKey) return; // silently skip identical re-init
      lastKey = key;
      return original(config);
    };
    id.__dsPatched = true;
  });
})();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <ThemeProvider>
          <Router>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/chat" element={<App />} />
              <Route path="/emergency" element={<Emergency />} />
            </Routes>
          </Router>
        </ThemeProvider>
      </AuthProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>
);
