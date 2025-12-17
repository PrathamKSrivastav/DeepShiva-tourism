import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEffect, useState } from "react";
import Hero from "./Hero";
import SeasonalEffects from "./SeasonalEffects";
import Footer from "./Footer";

function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/chat");
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-900 to-slate-950 text-white overflow-hidden relative">
      {/* Enhanced Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-tr from-indigo-950/40 via-transparent to-purple-900/40 pointer-events-none" />

      {/* Radial Gradient Overlay for depth */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full opacity-30 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(99,102,241,0.15) 0%, transparent 70%)",
        }}
      />

      {/* Background Effects */}
      <SeasonalEffects />

      {/* Content - Hero handles all login UI */}
      <div className="relative z-10">
        <Hero />
        <Footer />
      </div>
    </div>
  );
}

export default LandingPage;
