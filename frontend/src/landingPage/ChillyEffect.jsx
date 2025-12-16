import React, { useMemo } from 'react'
import { motion } from 'framer-motion'

export default function ChillyEffect() {
  // Generate snowflakes
  const snowflakes = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      size: Math.random() * 12 + 6, // 6-18px
      delay: Math.random() * 20, // ✅ INCREASED from 5 to 20 - better distribution
      duration: Math.random() * 8 + 10, // 10-18s
      drift: Math.random() * 80 - 40, // -40 to 40px horizontal drift
      opacity: Math.random() * 0.4 + 0.6, // 0.6-1.0
      blur: Math.random() * 1, // 0-1px
      rotation: Math.random() * 360,
    }))
  }, [])

  // Frost particles
  const frostParticles = useMemo(() => {
    return Array.from({ length: 25 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 6 + 3, // 3-9px
      delay: Math.random() * 10, // ✅ INCREASED for better spread
      duration: Math.random() * 2 + 1,
      opacity: Math.random() * 0.4 + 0.5, // 0.5-0.9
    }))
  }, [])

  return (
    <>
      {/* Continuous Falling Snowflakes */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
        {snowflakes.map((flake) => (
          <motion.div
            key={`snow-${flake.id}`}
            className="snowflake"
            initial={{ 
              y: -30,
              x: 0,
              opacity: flake.opacity, // ✅ START VISIBLE
              rotate: flake.rotation,
              scale: 1 // ✅ START AT FULL SIZE
            }}
            animate={{ 
              y: window.innerHeight + 50,
              x: [0, flake.drift, 0, -flake.drift, 0],
              opacity: flake.opacity, // ✅ STAY VISIBLE (no fade)
              rotate: [flake.rotation, flake.rotation + 360],
              scale: 1 // ✅ KEEP FULL SIZE
            }}
            transition={{
              duration: flake.duration,
              delay: flake.delay,
              repeat: Infinity, // ✅ Loop forever
              repeatDelay: 0, // ✅ NO GAP between loops
              ease: 'linear',
              x: {
                duration: flake.duration * 0.7,
                repeat: Infinity,
                ease: 'easeInOut'
              },
              rotate: {
                duration: flake.duration * 0.5,
                repeat: Infinity,
                ease: 'linear'
              }
            }}
            style={{
              position: 'absolute',
              left: flake.left,
              top: '-30px',
              width: `${flake.size}px`,
              height: `${flake.size}px`,
              filter: `blur(${flake.blur}px)`,
            }}
          />
        ))}
      </div>

      {/* Continuous Floating Frost Particles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
        {frostParticles.map((particle) => (
          <motion.div
            key={`frost-${particle.id}`}
            className="frost-particle"
            initial={{ 
              opacity: particle.opacity, // ✅ START VISIBLE
              scale: 1 // ✅ START AT FULL SIZE
            }}
            animate={{ 
              opacity: particle.opacity, // ✅ STAY VISIBLE
              scale: [1, 1.2, 1], // ✅ Subtle pulse
              y: [0, -30, 0], // ✅ Float up and back down
            }}
            transition={{
              duration: particle.duration,
              delay: particle.delay,
              repeat: Infinity,
              repeatDelay: 0, // ✅ NO GAP
              ease: 'easeInOut'
            }}
            style={{
              position: 'absolute',
              left: particle.left,
              top: particle.top,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
            }}
          />
        ))}
      </div>

      {/* Frost Vignette */}
      <div className="absolute inset-0 pointer-events-none z-5">
        <div className="frost-vignette-screen" />
      </div>
    </>
  )
}
