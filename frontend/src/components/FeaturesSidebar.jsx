import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MeditationSelector from "./MeditationSelector";
import YogaSelector from "./YogaSelector";

function FeaturesSidebar({ darkMode, isOpen, onToggle }) {
  const [isMobile, setIsMobile] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const [showMeditationModal, setShowMeditationModal] = useState(false);
  const [showYogaModal, setShowYogaModal] = useState(false);

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
      id: "yoga",
      name: "Yoga Practice",
      icon: "🤸",
      description: "AI-powered yoga pose detection and correction",
      color: "from-emerald-500 to-teal-600",
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
      onToggle?.(false); // ✅ Close sidebar immediately
    } else if (feature.id === "yoga") {
      setShowYogaModal(true);
      onToggle?.(false); // ✅ Close sidebar immediately
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
            onClick={() => onToggle?.(false)}
            className={`w-8 h-8 rounded-full flex items-center justify-center ${
              darkMode
                ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                : "bg-gray-100 hover:bg-gray-200 text-gray-700"
            }`}
          >
            ✕
          </button>
        )}
      </div>

      {/* Features List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {features.map((feature) => (
          <motion.div
            key={feature.id}
            whileHover={{ scale: 1.02 }}
            className="overflow-hidden"
          >
            <button
              onClick={() => handleFeatureClick(feature)}
              className={`w-full text-left p-4 rounded-xl transition-all ${
                activeFeature?.id === feature.id ||
                (feature.id === "meditation" && showMeditationModal) ||
                (feature.id === "yoga" && showYogaModal)
                  ? `bg-gradient-to-r ${feature.color} text-white shadow-lg`
                  : darkMode
                  ? "bg-dark-elev hover:bg-dark-elev/80 text-slate-200"
                  : "bg-white/60 hover:bg-white text-gray-800"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{feature.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm">{feature.name}</h3>
                    <p
                      className={`text-xs mt-0.5 ${
                        activeFeature?.id === feature.id ||
                        (feature.id === "meditation" && showMeditationModal) ||
                        (feature.id === "yoga" && showYogaModal)
                          ? "text-white/80"
                          : darkMode
                          ? "text-slate-400"
                          : "text-gray-600"
                      }`}
                    >
                      {feature.description}
                    </p>
                  </div>
                </div>
                {feature.id !== "meditation" && feature.id !== "yoga" && (
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

        {/* Modals - Render outside sidebar */}
        {showMeditationModal && (
          <MeditationSelector
            darkMode={darkMode}
            onClose={() => setShowMeditationModal(false)}
          />
        )}
        {showYogaModal && (
          <YogaSelector
            darkMode={darkMode}
            onClose={() => setShowYogaModal(false)}
          />
        )}
      </>
    );
  }

  // Mobile view - overlay only (button moved to header)
  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={() => onToggle?.(false)}
          />
          <aside className="fixed right-0 top-0 bottom-0 w-80 z-50">
            <SidebarContent />
          </aside>
        </>
      )}

      {/* Modals - Render OUTSIDE sidebar with higher z-index */}
      {showMeditationModal && (
        <MeditationSelector
          darkMode={darkMode}
          onClose={() => {
            setShowMeditationModal(false);
          }}
        />
      )}
      {showYogaModal && (
        <YogaSelector
          darkMode={darkMode}
          onClose={() => {
            setShowYogaModal(false);
          }}
        />
      )}
    </>
  );
}

// Weather Content Component
function WeatherContent({ darkMode }) {
  const weatherTips = [
    { temp: "25°C", condition: "Sunny", advice: "Perfect for temple visits" },
    { temp: "18°C", condition: "Pleasant", advice: "Ideal for trekking" },
    { temp: "12°C", condition: "Cool", advice: "Carry warm clothing" },
  ];

  return (
    <div className="space-y-2">
      {weatherTips.map((tip, idx) => (
        <div
          key={idx}
          className={`p-3 rounded-lg ${
            darkMode ? "bg-dark-surface" : "bg-white/60"
          }`}
        >
          <div className="flex items-center justify-between mb-1">
            <span
              className={`text-sm font-medium ${
                darkMode ? "text-slate-100" : "text-gray-800"
              }`}
            >
              {tip.condition}
            </span>
            <span
              className={`text-sm font-bold ${
                darkMode ? "text-emerald-400" : "text-emerald-600"
              }`}
            >
              {tip.temp}
            </span>
          </div>
          <p
            className={`text-xs ${
              darkMode ? "text-dark-muted" : "text-gray-600"
            }`}
          >
            {tip.advice}
          </p>
        </div>
      ))}
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
    "Dress modestly at religious sites",
    "Remove shoes before entering temples",
    "Carry enough water and snacks",
    "Book accommodations in advance",
  ];

  return (
    <ul className="space-y-2">
      {tips.map((tip, idx) => (
        <li
          key={idx}
          className={`text-sm ${darkMode ? "text-slate-200" : "text-gray-700"}`}
        >
          • {tip}
        </li>
      ))}
    </ul>
  );
}

export default FeaturesSidebar;
