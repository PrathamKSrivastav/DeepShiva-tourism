import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useYoga } from "../hooks/useYoga";
import YogaPractice from "./YogaPractice";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const POSE_CATEGORIES = {
  beginner: { icon: "🌱", color: "from-green-500 to-emerald-600" },
  intermediate: { icon: "🌿", color: "from-blue-500 to-cyan-600" },
  advanced: { icon: "🌳", color: "from-purple-500 to-pink-600" },
  all: { icon: "🧘", color: "from-orange-500 to-red-600" },
};

const YogaSelector = ({ darkMode, onClose }) => {
  const [stage, setStage] = useState("poses");
  const [selectedPose, setSelectedPose] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("all");

  const {
    availablePoses = [], // Default to empty array
    poseDetails,
    isLoading,
    error,
    fetchAvailablePoses,
    fetchPoseDetails,
  } = useYoga();

  useEffect(() => {
    console.log("🔄 YogaSelector mounted, fetching poses...");
    fetchAvailablePoses();
  }, [fetchAvailablePoses]);

  // Debug log
  useEffect(() => {
    console.log("📊 Available poses updated:", availablePoses);
  }, [availablePoses]);

  const handlePoseSelect = async (poseName) => {
    console.log("🎯 Pose selected:", poseName);
    setSelectedPose(poseName);

    try {
      const result = await fetchPoseDetails(poseName);
      console.log("✅ Pose details fetched:", result);

      if (result && result.success) {
        setStage("practice");
      } else {
        console.error("❌ No pose details received");
        alert("Failed to load pose details. Please try again.");
      }
    } catch (err) {
      console.error("❌ Failed to fetch pose details:", err);
      alert("Failed to load pose details. Please try again.");
    }
  };

  const handleBack = () => {
    if (stage === "practice") {
      setStage("poses");
      setSelectedPose(null);
    }
  };

  const filteredPoses = Array.isArray(availablePoses)
    ? availablePoses.filter((pose) => {
        if (selectedCategory === "all") return true;
        // Filter by difficulty category
        return pose.difficulty === selectedCategory;
      })
    : [];

  return (
    <>
      <AnimatePresence>
        {stage === "poses" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4 ${
              darkMode ? "bg-black/70" : "bg-black/60"
            }`}
            onClick={onClose}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`relative w-full max-w-4xl h-[95vh] sm:h-[90vh] sm:max-h-[85vh] rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl ${
                darkMode
                  ? "bg-dark-surface border border-dark-border"
                  : "bg-white border border-white/20"
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div
                className={`p-4 sm:p-6 border-b ${
                  darkMode ? "border-dark-border" : "border-white/20"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h2
                      className={`text-xl sm:text-2xl md:text-3xl font-bold mb-1 sm:mb-2 ${
                        darkMode ? "text-white" : "text-gray-900"
                      }`}
                    >
                      🧘 Yoga Practice
                    </h2>
                    <p
                      className={`text-xs sm:text-sm ${
                        darkMode ? "text-dark-muted" : "text-gray-600"
                      }`}
                    >
                      AI-powered pose detection
                    </p>
                  </div>
                  <button
                    onClick={onClose}
                    className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center transition-all hover:scale-110 flex-shrink-0 ml-2 ${
                      darkMode
                        ? "bg-dark-elev hover:bg-dark-elev/80 text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    ✕
                  </button>
                </div>

                {/* Category Filter */}
                <div className="flex gap-1.5 sm:gap-2 mt-3 sm:mt-4 flex-wrap">
                  {Object.entries(POSE_CATEGORIES).map(([key, data]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedCategory(key)}
                      className={`px-2.5 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all ${
                        selectedCategory === key
                          ? `bg-gradient-to-r ${data.color} text-white shadow-lg`
                          : darkMode
                          ? "bg-dark-elev text-dark-muted hover:bg-dark-elev/80"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      <span className="inline sm:hidden">{data.icon}</span>
                      <span className="hidden sm:inline">
                        {data.icon} {key.charAt(0).toUpperCase() + key.slice(1)}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Content */}
              <div className="overflow-y-auto no-scrollbar p-3 sm:p-6 h-[calc(95vh-140px)] sm:h-auto sm:max-h-[calc(85vh-180px)]">
                {isLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500" />
                  </div>
                ) : error ? (
                  <div
                    className={`p-4 rounded-lg text-center ${
                      darkMode
                        ? "bg-red-900/20 text-red-400"
                        : "bg-red-50 text-red-600"
                    }`}
                  >
                    Error loading poses: {error}
                  </div>
                ) : filteredPoses.length === 0 ? (
                  <div
                    className={`p-4 rounded-lg text-center ${
                      darkMode
                        ? "bg-yellow-900/20 text-yellow-400"
                        : "bg-yellow-50 text-yellow-600"
                    }`}
                  >
                    No yoga poses available. Please check backend configuration.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                    {filteredPoses.map((pose) => (
                      <motion.button
                        key={pose.name}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handlePoseSelect(pose.name)}
                        className={`p-4 sm:p-6 rounded-xl sm:rounded-2xl text-left transition-all overflow-hidden ${
                          darkMode
                            ? "bg-dark-elev hover:bg-dark-elev/80 border border-dark-border"
                            : "bg-white/60 hover:bg-white border border-white/20"
                        }`}
                      >
                        <div className="w-full h-28 sm:h-32 mb-2 sm:mb-3 rounded-lg sm:rounded-xl overflow-hidden flex items-center justify-center bg-gradient-to-br from-emerald-500/10 to-emerald-600/10">
                          {pose.image ? (
                            <img
                              src={`${API_URL}/yoga-static/img/${pose.image}`}
                              alt={pose.display_name}
                              className="w-full h-full object-cover"
                              style={{
                                mixBlendMode: darkMode ? "screen" : "multiply",
                                filter: "contrast(1.1) brightness(1.05)",
                              }}
                              onError={(e) => {
                                e.target.style.display = "none";
                                e.target.nextSibling.style.display = "flex";
                              }}
                            />
                          ) : null}
                          <span
                            className="text-6xl"
                            style={{
                              display: pose.image ? "none" : "flex",
                            }}
                          >
                            🧘
                          </span>
                        </div>

                        <h3
                          className={`text-sm sm:text-base font-bold mb-1 sm:mb-2 ${
                            darkMode ? "text-white" : "text-gray-900"
                          }`}
                        >
                          {pose.display_name}
                        </h3>

                        {pose.description && (
                          <p
                            className={`text-xs mb-2 sm:mb-3 line-clamp-2 ${
                              darkMode ? "text-dark-muted" : "text-gray-600"
                            }`}
                          >
                            {pose.description}
                          </p>
                        )}

                        <div className="flex items-center justify-between gap-1.5 sm:gap-2">
                          <span
                            className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full ${
                              darkMode
                                ? "bg-dark-surface text-dark-muted"
                                : "bg-gray-100 text-gray-600"
                            }`}
                          >
                            {pose.difficulty || "Beginner"}
                          </span>
                          {pose.duration && (
                            <span
                              className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full flex items-center gap-0.5 sm:gap-1 ${
                                darkMode
                                  ? "bg-emerald-900/30 text-emerald-400"
                                  : "bg-emerald-100 text-emerald-700"
                              }`}
                            >
                              ⏱️ {pose.duration}s
                            </span>
                          )}
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* Practice stage */}
        {stage === "practice" && selectedPose && poseDetails && (
          <YogaPractice
            poseName={selectedPose}
            poseDetails={poseDetails}
            onClose={handleBack}
            darkMode={darkMode}
          />
        )}
      </AnimatePresence>
    </>
  );
};

export default YogaSelector;
