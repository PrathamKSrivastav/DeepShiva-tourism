import React, { useMemo } from "react";
import { motion } from "framer-motion";

export default function SeasonalEffects({ season, containerHeight = 600 }) {
  // Snowflakes for Winter
  const snowflakes = useMemo(() => {
    if (season !== "winter") return [];
    return Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 12 + 6,
      delay: Math.random() * 20,
      duration: Math.random() * 8 + 10,
      drift: Math.random() * 80 - 40,
      opacity: Math.random() * 0.4 + 0.6,
      blur: Math.random() * 1,
      rotation: Math.random() * 360,
    }));
  }, [season]);

  // Falling Leaves for Autumn
  const leaves = useMemo(() => {
    if (season !== "autumn") return [];
    return Array.from({ length: 30 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 15 + 10,
      delay: Math.random() * 15,
      duration: Math.random() * 6 + 8,
      drift: Math.random() * 120 - 60,
      rotation: Math.random() * 360,
      color: ["#ff6b35", "#f7931e", "#c1440e", "#8b4513"][
        Math.floor(Math.random() * 4)
      ],
    }));
  }, [season]);

  // Cherry Blossoms for Spring
  const petals = useMemo(() => {
    if (season !== "spring") return [];
    return Array.from({ length: 40 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 10 + 5,
      delay: Math.random() * 18,
      duration: Math.random() * 7 + 10,
      drift: Math.random() * 100 - 50,
      rotation: Math.random() * 360,
    }));
  }, [season]);

  // Fireflies for Summer
  const fireflies = useMemo(() => {
    if (season !== "summer") return [];
    return Array.from({ length: 20 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 4 + 3,
      delay: Math.random() * 5,
    }));
  }, [season]);

  return (
    <>
      {/* WINTER - Snowflakes */}
      {season === "winter" && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
          {snowflakes.map((flake) => (
            <motion.div
              key={`snow-${flake.id}`}
              className="snowflake"
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
              }}
            />
          ))}
        </div>
      )}

      {/* AUTUMN - Falling Leaves */}
      {season === "autumn" && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
          {leaves.map((leaf) => (
            <motion.div
              key={`leaf-${leaf.id}`}
              className="autumn-leaf"
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
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
          {petals.map((petal) => (
            <motion.div
              key={`petal-${petal.id}`}
              className="cherry-petal"
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
              }}
            />
          ))}
        </div>
      )}

      {/* SUMMER - Fireflies */}
      {season === "summer" && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
          {fireflies.map((fly) => (
            <motion.div
              key={`fly-${fly.id}`}
              className="firefly"
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
              }}
            />
          ))}
        </div>
      )}
    </>
  );
}
