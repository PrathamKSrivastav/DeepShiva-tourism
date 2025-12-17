import React, { useMemo } from "react";
import { motion } from "framer-motion";

export default function SeasonalEffects({ season, containerHeight = 600 }) {
  // Snowflakes for Winter
  const snowflakes = useMemo(() => {
    if (season !== "winter") return [];
    return Array.from({ length: 35 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 8 + 4,
      delay: Math.random() * 15,
      duration: Math.random() * 6 + 8,
      drift: Math.random() * 60 - 30,
      opacity: Math.random() * 0.5 + 0.5,
      blur: Math.random() * 0.5,
      rotation: Math.random() * 360,
    }));
  }, [season]);

  // Falling Leaves for Autumn
  const leaves = useMemo(() => {
    if (season !== "autumn") return [];
    return Array.from({ length: 25 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 12 + 8,
      delay: Math.random() * 12,
      duration: Math.random() * 5 + 6,
      drift: Math.random() * 80 - 40,
      rotation: Math.random() * 360,
      color: ["#ff6b35", "#f7931e", "#c1440e", "#8b4513"][
        Math.floor(Math.random() * 4)
      ],
    }));
  }, [season]);

  // Cherry Blossoms for Spring
  const petals = useMemo(() => {
    if (season !== "spring") return [];
    return Array.from({ length: 30 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 8 + 4,
      delay: Math.random() * 14,
      duration: Math.random() * 6 + 8,
      drift: Math.random() * 70 - 35,
      rotation: Math.random() * 360,
    }));
  }, [season]);

  // Fireflies for Summer
  const fireflies = useMemo(() => {
    if (season !== "summer") return [];
    return Array.from({ length: 15 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 3 + 2,
      delay: Math.random() * 4,
    }));
  }, [season]);

  return (
    <>
      {/* WINTER - Snowflakes */}
      {season === "winter" && (
        <div className="absolute inset-0 pointer-events-none">
          {snowflakes.map((flake) => (
            <motion.div
              key={`snow-${flake.id}`}
              className="snowflake bg-white rounded-full" // Added bg-white and rounded-full explicitly
              initial={{
                y: -30,
                x: 0,
                opacity: flake.opacity,
                rotate: flake.rotation,
                scale: 1,
              }}
              animate={{
                y: containerHeight + 50,
                x: [0, flake.drift, 0, -flake.drift, 0],
                opacity: flake.opacity,
                rotate: [flake.rotation, flake.rotation + 360],
                scale: 1,
              }}
              transition={{
                duration: flake.duration,
                delay: flake.delay,
                repeat: Infinity,
                repeatDelay: 0,
                ease: "linear",
                x: {
                  duration: flake.duration * 0.7,
                  repeat: Infinity,
                  ease: "easeInOut",
                },
                rotate: {
                  duration: flake.duration * 0.5,
                  repeat: Infinity,
                  ease: "linear",
                },
              }}
              style={{
                position: "absolute",
                left: flake.left,
                top: "-30px",
                width: `${flake.size}px`,
                height: `${flake.size}px`,
                filter: `blur(${flake.blur}px)`,
                backgroundColor: "white", // Ensure color is set
                boxShadow: "0 0 5px rgba(255,255,255,0.8)", // Add glow
              }}
            />
          ))}
        </div>
      )}

      {/* AUTUMN - Falling Leaves */}
      {season === "autumn" && (
        <div className="absolute inset-0 pointer-events-none">
          {leaves.map((leaf) => (
            <motion.div
              key={`leaf-${leaf.id}`}
              className="autumn-leaf rounded-tl-none rounded-br-none rounded-tr-full rounded-bl-full" // Leaf shape
              initial={{ y: -30, x: 0, rotate: leaf.rotation, scale: 1 }}
              animate={{
                y: containerHeight + 50,
                x: [0, leaf.drift, -leaf.drift / 2, leaf.drift / 2, 0],
                rotate: [leaf.rotation, leaf.rotation + 720],
                scale: [1, 0.8, 1, 0.9, 1],
              }}
              transition={{
                duration: leaf.duration,
                delay: leaf.delay,
                repeat: Infinity,
                repeatDelay: 0,
                ease: "easeInOut",
              }}
              style={{
                position: "absolute",
                left: leaf.left,
                top: "-30px",
                width: `${leaf.size}px`,
                height: `${leaf.size}px`,
                backgroundColor: leaf.color,
              }}
            />
          ))}
        </div>
      )}

      {/* SPRING - Cherry Blossom Petals */}
      {season === "spring" && (
        <div className="absolute inset-0 pointer-events-none">
          {petals.map((petal) => (
            <motion.div
              key={`petal-${petal.id}`}
              className="cherry-petal rounded-full"
              initial={{ y: -30, x: 0, rotate: petal.rotation, scale: 1 }}
              animate={{
                y: containerHeight + 50,
                x: [0, petal.drift, -petal.drift, petal.drift / 2, 0],
                rotate: [petal.rotation, petal.rotation + 360],
                scale: [1, 1.2, 0.8, 1],
              }}
              transition={{
                duration: petal.duration,
                delay: petal.delay,
                repeat: Infinity,
                repeatDelay: 0,
                ease: "easeInOut",
              }}
              style={{
                position: "absolute",
                left: petal.left,
                top: "-30px",
                width: `${petal.size}px`,
                height: `${petal.size}px`,
                backgroundColor: "#ffb7b2", // Pink color
                boxShadow: "0 0 5px rgba(255, 183, 178, 0.6)",
              }}
            />
          ))}
        </div>
      )}

      {/* SUMMER - Fireflies */}
      {season === "summer" && (
        <div className="absolute inset-0 pointer-events-none">
          {fireflies.map((fly) => (
            <motion.div
              key={`fly-${fly.id}`}
              className="firefly rounded-full"
              initial={{ opacity: 0, scale: 0 }}
              animate={{
                opacity: [0, 1, 1, 0],
                scale: [0, 1.5, 1, 0],
                x: [0, 20, -10, 15, 0],
                y: [0, -15, -25, -10, 0],
              }}
              transition={{
                duration: 3,
                delay: fly.delay,
                repeat: Infinity,
                repeatDelay: 2,
                ease: "easeInOut",
              }}
              style={{
                position: "absolute",
                left: fly.left,
                top: fly.top,
                width: `${fly.size}px`,
                height: `${fly.size}px`,
                backgroundColor: "#fbbf24", // Yellow/Gold
                boxShadow: "0 0 8px 2px rgba(251, 191, 36, 0.8)", // Strong glow
              }}
            />
          ))}
        </div>
      )}
    </>
  );
}