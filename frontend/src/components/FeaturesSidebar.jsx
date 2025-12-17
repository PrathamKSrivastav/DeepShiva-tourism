import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MeditationSelector from "./MeditationSelector";

function FeaturesSidebar({ darkMode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const [showMeditationModal, setShowMeditationModal] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const features = [
    {
      id: "meditation",
      name: "Meditation",
      icon: "🧘",
      description: "Guided meditation courses for spiritual journeys",
      color: "from-purple-500 to-indigo-600",
    },
    {
      id: "weather",
      name: "Weather",
      icon: "🌤️",
      description: "Real-time weather updates for destinations",
      color: "from-blue-500 to-cyan-600",
    },
    {
      id: "festivals",
      name: "Festivals",
      icon: "🎉",
      description: "Upcoming festivals and celebrations",
      color: "from-orange-500 to-red-600",
    },
    {
      id: "tips",
      name: "Travel Tips",
      icon: "💡",
      description: "Essential tips for your journey",
      color: "from-emerald-500 to-teal-600",
    },
  ];

  const handleFeatureClick = (feature) => {
    if (feature.id === "meditation") {
      setShowMeditationModal(true);
    } else {
      setActiveFeature(activeFeature?.id === feature.id ? null : feature);
    }
  };

  const SidebarContent = () => (
    <div
      className={`h-full flex flex-col ${
        darkMode
          ? "bg-dark-surface border-l border-dark-border"
          : "bg-white/40 backdrop-blur-xl border-white/20"
      }`}
    >
      {/* Header */}
      <div
        className={`p-5 flex items-center justify-between border-b ${
          darkMode ? "border-dark-border" : "border-white/20"
        }`}
      >
        <h2
          className={`font-semibold tracking-tight ${
            darkMode ? "text-slate-100" : "text-gray-800"
          }`}
        >
          Features
        </h2>
        {isMobile && (
          <button
            onClick={() => setIsOpen(false)}
            className={`p-1 rounded-full transition-colors ${
              darkMode
                ? "text-gray-400 hover:bg-dark-elev/60"
                : "text-gray-500 hover:bg-black/5"
            }`}
          >
            ✕
          </button>
        )}
      </div>

      {/* Features List */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-2">
        {features.map((feature) => (
          <motion.div
            key={feature.id}
            initial={false}
            animate={{
              height: activeFeature?.id === feature.id ? "auto" : "auto",
            }}
          >
            <button
              onClick={() => handleFeatureClick(feature)}
              className={`w-full text-left p-4 rounded-xl transition-all duration-200 ${
                activeFeature?.id === feature.id
                  ? darkMode
                    ? "bg-dark-elev ring-1 ring-emerald-500/30 shadow-lg"
                    : "bg-white ring-1 ring-emerald-200 shadow-lg"
                  : darkMode
                  ? "bg-dark-surface/40 hover:bg-dark-elev/60"
                  : "bg-white/30 hover:bg-white/50"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-2xl shadow-md`}
                >
                  {feature.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h3
                    className={`font-semibold text-sm ${
                      darkMode ? "text-slate-100" : "text-gray-800"
                    }`}
                  >
                    {feature.name}
                  </h3>
                  <p
                    className={`text-xs ${
                      darkMode ? "text-dark-muted" : "text-gray-500"
                    }`}
                  >
                    {feature.description}
                  </p>
                </div>
                {feature.id !== "meditation" && (
                  <svg
                    className={`w-5 h-5 transition-transform ${
                      activeFeature?.id === feature.id ? "rotate-180" : ""
                    } ${darkMode ? "text-slate-400" : "text-gray-500"}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                )}
              </div>
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
              {activeFeature?.id === feature.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div
                    className={`mt-2 p-4 rounded-xl ${
                      darkMode
                        ? "bg-dark-elev/50 border border-dark-border"
                        : "bg-white/60 border border-white/60"
                    }`}
                  >
                    {feature.id === "weather" && (
                      <WeatherContent darkMode={darkMode} />
                    )}
                    {feature.id === "festivals" && (
                      <FestivalsContent darkMode={darkMode} />
                    )}
                    {feature.id === "tips" && (
                      <TipsContent darkMode={darkMode} />
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );

  // Desktop view
  if (!isMobile) {
    return (
      <>
        <aside className="w-80 h-full flex-shrink-0 relative z-10">
          <SidebarContent />
        </aside>
        {showMeditationModal && (
          <MeditationSelector
            darkMode={darkMode}
            onClose={() => setShowMeditationModal(false)}
          />
        )}
      </>
    );
  }

  // Mobile view - Floating button + overlay
  return (
    <>
      {/* Floating Features Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center text-2xl z-40 transition-transform hover:scale-110 ${
          darkMode
            ? "bg-gradient-to-br from-emerald-500 to-emerald-600"
            : "bg-gradient-to-br from-emerald-500 to-emerald-600"
        }`}
        style={{
          boxShadow: "0 8px 32px rgba(16, 185, 129, 0.4)",
        }}
      >
        ✨
      </button>

      {/* Mobile Overlay */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={() => setIsOpen(false)}
          />
          <aside className="fixed right-0 top-0 bottom-0 w-80 z-50">
            <SidebarContent />
          </aside>
        </>
      )}

      {showMeditationModal && (
        <MeditationSelector
          darkMode={darkMode}
          onClose={() => {
            setShowMeditationModal(false);
            setIsOpen(false);
          }}
        />
      )}
    </>
  );
}

// Weather Content Component
function WeatherContent({ darkMode }) {
  return (
    <div className="space-y-3">
      <div
        className={`p-3 rounded-lg ${
          darkMode ? "bg-dark-surface" : "bg-white/60"
        }`}
      >
        <p
          className={`text-xs ${
            darkMode ? "text-dark-muted" : "text-gray-600"
          }`}
        >
          Ask your guide about weather conditions for any destination
        </p>
      </div>
      <div className="flex gap-2">
        <button
          className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            darkMode
              ? "bg-dark-surface hover:bg-dark-elev text-slate-100"
              : "bg-white/60 hover:bg-white text-gray-700"
          }`}
        >
          🌦️ Kedarnath
        </button>
        <button
          className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            darkMode
              ? "bg-dark-surface hover:bg-dark-elev text-slate-100"
              : "bg-white/60 hover:bg-white text-gray-700"
          }`}
        >
          ☀️ Rishikesh
        </button>
      </div>
    </div>
  );
}

// Festivals Content Component
function FestivalsContent({ darkMode }) {
  const festivals = [
    { name: "Kumbh Mela", date: "April 2025" },
    { name: "Char Dham Yatra", date: "May-Nov 2025" },
    { name: "Ganga Dussehra", date: "June 2025" },
  ];

  return (
    <div className="space-y-2">
      {festivals.map((fest) => (
        <div
          key={fest.name}
          className={`p-3 rounded-lg ${
            darkMode ? "bg-dark-surface" : "bg-white/60"
          }`}
        >
          <p
            className={`text-sm font-medium ${
              darkMode ? "text-slate-100" : "text-gray-800"
            }`}
          >
            {fest.name}
          </p>
          <p
            className={`text-xs ${
              darkMode ? "text-dark-muted" : "text-gray-500"
            }`}
          >
            {fest.date}
          </p>
        </div>
      ))}
    </div>
  );
}

// Tips Content Component
function TipsContent({ darkMode }) {
  const tips = [
    "📱 Download offline maps",
    "💧 Stay hydrated in hills",
    "🧥 Carry warm clothing",
    "💊 Pack basic medicines",
  ];

  return (
    <ul className="space-y-2">
      {tips.map((tip, idx) => (
        <li
          key={idx}
          className={`text-sm ${darkMode ? "text-slate-100" : "text-gray-700"}`}
        >
          {tip}
        </li>
      ))}
    </ul>
  );
}

export default FeaturesSidebar;
