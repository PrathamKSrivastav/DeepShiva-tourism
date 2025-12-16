import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { GoogleLogin } from "@react-oauth/google";

export default function LoginPanel() {
  const [hoveredButton, setHoveredButton] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleGuestClick = () => {
    console.log("👤 Continuing as guest");
    navigate("/chat");
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setIsLoading(true);
    console.log("🎫 Google credential received");
    const result = await login(credentialResponse.credential);

    if (result.success) {
      console.log("✅ Login complete:", result.user.email);
      setTimeout(() => {
        navigate("/chat");
      }, 500);
    } else {
      console.error("❌ Login failed:", result.error);
      alert(`Login failed: ${result.error}`);
      setIsLoading(false);
    }
  };

  const handleGoogleError = () => {
    console.error("❌ Google Login Failed");
    alert("Google Login failed. Please try again.");
    setIsLoading(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.6,
        delay: 0.1,
        ease: [0.22, 1, 0.36, 1],
      }}
      className="w-full max-w-md bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-8 lg:p-10"
    >
      {/* Header */}
      <div className="text-center mb-8">
        <motion.h2
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.3,
            duration: 0.5,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="text-3xl md:text-4xl font-bold text-gray-900 mb-3"
        >
          Get Started
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            delay: 0.4,
            duration: 0.5,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="text-gray-600 text-sm md:text-base"
        >
          Begin your journey to discover amazing destinations
        </motion.p>
      </div>

      {/* Buttons */}
      <div className="space-y-4">
        {/* Google Login Button */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.5,
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="w-full"
        >
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap={false}
            theme="filled_white"
            size="large"
            text="signin_with"
            shape="rounded"
            auto_select={false}
            disabled={isLoading}
          />
        </motion.div>

        {/* Divider */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            delay: 0.6,
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
          className="relative flex items-center justify-center my-6"
        >
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300"></div>
          </div>
          <span className="relative bg-white px-4 text-sm text-gray-500">
            or
          </span>
        </motion.div>

        {/* Continue as Guest */}
        <motion.button
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.7,
            duration: 0.4,
            ease: [0.22, 1, 0.36, 1],
          }}
          onClick={handleGuestClick}
          onHoverStart={() => setHoveredButton("guest")}
          onHoverEnd={() => setHoveredButton(null)}
          whileHover={{ scale: 1.02, y: -2 }}
          whileTap={{ scale: 0.98 }}
          disabled={isLoading}
          className="w-full px-6 py-3 rounded-xl bg-gradient-to-r from-accent-indigo to-accent-fuchsia backdrop-blur-md overflow-hidden border border-indigo-400/30 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed relative font-semibold text-base"
        >
          <motion.div
            className="absolute inset-0 bg-indigo-600/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: hoveredButton === "guest" ? 1 : 0 }}
            transition={{ duration: 0.25 }}
          />
          <span className="relative z-10 text-white font-semibold text-base flex items-center justify-center gap-2">
            Continue as Guest
            <motion.span
              animate={{ x: hoveredButton === "guest" ? 5 : 0 }}
              transition={{ duration: 0.15 }}
            >
              →
            </motion.span>
          </span>
        </motion.button>
      </div>

      {/* Footer Note */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{
          delay: 0.8,
          duration: 0.5,
          ease: [0.22, 1, 0.36, 1],
        }}
        className="text-center text-xs text-gray-500 mt-6"
      >
        By continuing, you agree to our Terms & Privacy Policy
      </motion.p>
    </motion.div>
  );
}
