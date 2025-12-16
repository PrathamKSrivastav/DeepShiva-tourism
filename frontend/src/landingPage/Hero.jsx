import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Monitor3D from "./Monitor3D";
import LoginPanel from "./LoginPanel";
import SeasonToggle from "./SeasonToggle";
import { seasons, seasonOrder } from "./seasonConfig";

export default function Hero() {
  const [animationStage, setAnimationStage] = useState("rotate");
  const [currentSeason, setCurrentSeason] = useState("winter");
  const [isRotating, setIsRotating] = useState(false);

  useEffect(() => {
    const rotationTimer = setTimeout(() => {
      setAnimationStage("content");
    }, 3000);

    return () => {
      clearTimeout(rotationTimer);
    };
  }, []);

  const handleSeasonChange = () => {
    setIsRotating(true);
    const currentIndex = seasonOrder.indexOf(currentSeason);
    const nextIndex = (currentIndex + 1) % seasonOrder.length;
    setCurrentSeason(seasonOrder[nextIndex]);

    setTimeout(() => setIsRotating(false), 2000);
  };

  const seasonData = seasons[currentSeason];

  return (
    <section className="relative w-full h-screen overflow-hidden">
      {/* DYNAMIC SEASONAL GRADIENT BACKGROUND */}
      <div className="absolute inset-0 z-0">
        <div
          className={`absolute inset-0 bg-gradient-to-br ${seasonData.gradient.base} transition-colors duration-1000`}
        />

        {/* Animated mesh layers with seasonal colors */}
        <div
          className="gradient-mesh-1"
          style={{
            background: `radial-gradient(circle at center, ${
              seasonData.gradient.mesh1
            } 0%, ${seasonData.gradient.mesh1.replace(
              "0.3",
              "0.15"
            )} 25%, transparent 70%)`,
          }}
        />
        <div
          className="gradient-mesh-2"
          style={{
            background: `radial-gradient(ellipse at center, ${
              seasonData.gradient.mesh2
            } 0%, ${seasonData.gradient.mesh2.replace(
              "0.2",
              "0.12"
            )} 30%, transparent 65%)`,
          }}
        />
        <div
          className="gradient-mesh-3"
          style={{
            background: `radial-gradient(circle at center, ${
              seasonData.gradient.mesh3
            } 0%, ${seasonData.gradient.mesh3.replace(
              "0.18",
              "0.08"
            )} 35%, transparent 60%)`,
          }}
        />

        <div className="absolute inset-0 opacity-[0.015] mix-blend-overlay">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
            }}
          />
        </div>
      </div>

      {/* SEASON TOGGLE BUTTON */}
      <SeasonToggle
        currentSeason={currentSeason}
        onSeasonChange={handleSeasonChange}
        isRotating={isRotating}
      />

      {/* MAIN CONTENT */}
      <div className="relative z-10 w-full h-full flex items-center justify-center px-6 lg:px-12">
        <div className="w-full max-w-7xl mx-auto flex items-center justify-center lg:justify-between gap-8">
          {/* MONITOR */}
          <motion.div
            initial={{ rotateX: 90, opacity: 0, y: 30, scale: 1, x: 0 }}
            animate={{
              rotateX: 0,
              opacity: 1,
              y: 0,
              scale: animationStage === "content" ? 1.1 : 1,
              x: animationStage === "content" ? "-10%" : 0,
            }}
            transition={{
              rotateX: { duration: 2.2, ease: [0.22, 1, 0.36, 1] },
              opacity: { duration: 0.5, delay: 0.2 },
              y: { duration: 1.5, ease: [0.22, 1, 0.36, 1] },
              scale: { duration: 1, ease: [0.22, 1, 0.36, 1] },
              x: { duration: 1, ease: [0.22, 1, 0.36, 1] },
            }}
            className="w-full max-w-3xl flex-shrink-0"
            style={{ perspective: "2500px", transformStyle: "preserve-3d" }}
          >
            <Monitor3D season={currentSeason} seasonData={seasonData} />
          </motion.div>

          {/* LOGIN PANEL */}
          <AnimatePresence>
            {animationStage === "content" && (
              <motion.div
                initial={{ opacity: 0, x: 80 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0 }}
                className="w-full max-w-md flex-shrink-0 relative z-20"
              >
                {/* LoginPanel component handles all button interactions */}
                <LoginPanel />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Footer */}
      <AnimatePresence>
        {animationStage === "content" && (
          <motion.footer
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.8 }}
            className="fixed bottom-6 left-0 right-0 z-30 text-center"
          >
            <p className="text-sm text-gray-500 font-light tracking-wide">
              Built by team{" "}
              <span className="text-primary-dark font-medium">resMLAI</span>
            </p>
          </motion.footer>
        )}
      </AnimatePresence>
    </section>
  );
}
