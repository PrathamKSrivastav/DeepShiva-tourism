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
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  // Detect screen size changes with smooth transition
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 890); // Mobile: < 890px
      setIsTablet(width >= 890 && width < 1300); // Tablet: 890px - 1300px
    };

    // Initial check
    checkScreenSize();

    // Add resize listener with debounce
    let timeoutId;
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(checkScreenSize, 150);
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      clearTimeout(timeoutId);
    };
  }, []);

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
    <section className="relative w-full h-screen overflow-hidden bg-white">
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

      {/* MAIN CONTENT - Animated transition between layouts */}
      <div className="relative z-10 w-full h-screen flex items-center justify-center overflow-hidden">
        <AnimatePresence mode="wait">
          {isMobile ? (
            // MOBILE LAYOUT (< 768px)
            <motion.div
              key="mobile-layout"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
              className="w-full h-full relative"
            >
              {/* Background Hero Image - flows from top to middle */}
              <motion.div
                key={currentSeason}
                initial={{ opacity: 0, scale: 1.05 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8 }}
                className="absolute top-0 left-0 right-0 w-full h-[45vh] rounded-b-[1rem] overflow-hidden"
              >
                <img
                  src={seasonData.image}
                  alt={`${seasonData.name} landscape`}
                  className="w-full h-full object-cover"
                />

                {/* Explore Text Overlay */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.h2
                    initial={{ opacity: 0, scale: 0.92 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5, duration: 0.8 }}
                    className="text-white text-6xl font-bold"
                    style={{
                      fontFamily: "Georgia, serif",
                      fontStyle: "italic",
                      textShadow: `
                        0 4px 40px rgba(0,0,0,0.9),
                        0 8px 60px rgba(0,0,0,0.7)
                      `,
                    }}
                  >
                    Explore
                  </motion.h2>
                </div>
              </motion.div>

              {/* Overlayed Login Panel */}
              <AnimatePresence>
                {animationStage === "content" && (
                  <motion.div
                    initial={{ opacity: 0, y: 30, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{
                      duration: 0.8,
                      ease: [0.22, 1, 0.36, 1],
                      delay: 0.4,
                    }}
                    className="absolute top-[35vh] left-0 right-0 z-30 flex items-center justify-center px-6"
                  >
                    <div className="w-full max-w-md">
                      <LoginPanel />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ) : (
            // DESKTOP/TABLET LAYOUT (>= 768px)
            <motion.div
              key="desktop-layout"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
              className={`w-full mx-auto flex items-center justify-center px-4 ${
                isTablet
                  ? "max-w-5xl gap-6 flex-col md:flex-row scale-90"
                  : "max-w-7xl gap-20 px-6 lg:px-12"
              }`}
            >
              {/* Monitor3D - Responsive sizing */}
              <motion.div
                initial={{ rotateX: 90, opacity: 0, y: 30, scale: 1, x: 0 }}
                animate={{
                  rotateX: 0,
                  opacity: 1,
                  y: 0,
                  scale:
                    animationStage === "content"
                      ? isTablet
                        ? 0.9
                        : 1.05
                      : isTablet
                      ? 0.85
                      : 1,
                  x:
                    animationStage === "content"
                      ? isTablet
                        ? "0%"
                        : "-4%"
                      : 0,
                }}
                transition={{
                  rotateX: { duration: 2.2, ease: [0.22, 1, 0.36, 1] },
                  opacity: { duration: 0.5, delay: 0.2 },
                  y: { duration: 1.5, ease: [0.22, 1, 0.36, 1] },
                  scale: { duration: 1, ease: [0.22, 1, 0.36, 1] },
                  x: { duration: 1, ease: [0.22, 1, 0.36, 1] },
                }}
                className={`flex-shrink-0 ${
                  isTablet ? "w-full max-w-lg" : "w-full max-w-2xl"
                }`}
                style={{ perspective: "2500px", transformStyle: "preserve-3d" }}
              >
                <Monitor3D season={currentSeason} seasonData={seasonData} />
              </motion.div>

              {/* Login Panel - Responsive sizing */}
              <AnimatePresence>
                {animationStage === "content" && (
                  <motion.div
                    initial={{
                      opacity: 0,
                      x: isTablet ? 0 : 80,
                      y: isTablet ? 20 : 0,
                    }}
                    animate={{ opacity: 1, x: 0, y: 0 }}
                    transition={{
                      duration: 1,
                      ease: [0.22, 1, 0.36, 1],
                      delay: isTablet ? 0.2 : 0,
                    }}
                    className={`flex-shrink-0 relative z-20 ${
                      isTablet ? "w-full max-w-md px-4" : "w-full max-w-md"
                    }`}
                  >
                    <LoginPanel />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
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
              <span className="text-primary-dark font-medium">rasMLAI</span>
            </p>
          </motion.footer>
        )}
      </AnimatePresence>
    </section>
  );
}
