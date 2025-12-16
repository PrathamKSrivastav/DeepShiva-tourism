import React, { useRef, useEffect, useState } from "react";
import { motion } from "framer-motion";
import SeasonalEffects from "./SeasonalEffects";

export default function Monitor3D({ season, seasonData }) {
  const screenRef = useRef(null);
  const [screenHeight, setScreenHeight] = useState(600);

  useEffect(() => {
    if (screenRef.current) {
      setScreenHeight(screenRef.current.offsetHeight);
    }
  }, []);

  return (
    <div className="relative w-full">
      {/* Monitor Display */}
      <div className="relative rounded-3xl overflow-hidden shadow-2xl bg-gradient-to-b from-gray-800 to-gray-900 p-3">
        {/* Screen Bezel */}
        <div
          ref={screenRef}
          className="relative aspect-[16/10] bg-black rounded-2xl overflow-hidden"
        >
          {/* Display Content */}
          <div className="w-full h-full relative">
            {/* ✅ SEASONAL Mountain Background */}
            <motion.img
              key={season}
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
              src={seasonData.image}
              alt={`${season} Landscape`}
              className="w-full h-full object-cover"
            />

            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/20" />

            {/* ✅ SEASONAL EFFECTS - Pass container height */}
            <div className="absolute inset-0 overflow-hidden rounded-2xl">
              <SeasonalEffects season={season} containerHeight={screenHeight} />
            </div>

            {/* Top Bar Labels */}
            <div className="absolute top-4 left-6 text-white text-xs font-light opacity-90 drop-shadow-lg z-10">
              rasML·AI
            </div>

            {/* Center "Explore" Text */}
            <div className="absolute inset-0 flex items-center justify-center z-20">
              <motion.h2
                initial={{ opacity: 0, scale: 0.92, z: -10 }}
                animate={{ opacity: 1, scale: 1, z: 0 }}
                transition={{
                  delay: 2.5,
                  duration: 0.8,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="text-white text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold"
                style={{
                  fontFamily: "Georgia, serif",
                  fontStyle: "italic",
                  textShadow: `
                    0 4px 40px rgba(0,0,0,0.9),
                    0 8px 60px rgba(0,0,0,0.7),
                    0 2px 4px rgba(0,0,0,0.8),
                    0 0 30px rgba(255,255,255,0.2)
                  `,
                  transform: "translateZ(20px)",
                  filter: "drop-shadow(0 10px 25px rgba(0,0,0,0.5))",
                  WebkitTextStroke: "1px rgba(255,255,255,0.1)",
                  letterSpacing: "0.02em",
                }}
              >
                Explore
              </motion.h2>
            </div>

            {/* Screen Glare */}
            <motion.div
              animate={{ x: ["-100%", "200%"], opacity: [0, 0.15, 0] }}
              transition={{
                duration: 3,
                repeat: Infinity,
                repeatDelay: 4,
                ease: "easeInOut",
                delay: 4,
              }}
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent pointer-events-none z-20"
              style={{ width: "40%" }}
            />
          </div>
        </div>
      </div>

      {/* Monitor Stand */}
      <div className="relative flex flex-col items-center mt-1">
        <div className="w-32 h-6 bg-gradient-to-b from-gray-800 to-gray-700 rounded-b-xl shadow-lg" />
        <div className="w-6 h-16 bg-gradient-to-r from-gray-300 via-gray-200 to-gray-300 rounded-b-lg shadow-md" />
        <div className="w-48 h-3 bg-gradient-to-r from-gray-400 via-gray-300 to-gray-400 rounded-full shadow-lg" />
      </div>

      {/* Shadow */}
      <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-2/3 h-8 bg-black/10 blur-2xl rounded-full" />
    </div>
  );
}
