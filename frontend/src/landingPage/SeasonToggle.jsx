import React, { useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import * as THREE from 'three'
import Earth3D from './Earth3D'

// Earth texture URLs for each season
const seasonTextures = {
  winter: 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg',
  spring: 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg',
  summer: 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg',
  autumn: 'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/planets/earth_atmos_2048.jpg'
}

export default function SeasonToggle({ currentSeason, onSeasonChange, isRotating }) {
  // Load Earth texture
  const earthTexture = useMemo(() => {
    const loader = new THREE.TextureLoader()
    return loader.load(seasonTextures[currentSeason])
  }, [currentSeason])

  return (
    <button
      onClick={onSeasonChange}
      className="fixed top-6 right-12 z-50 group cursor-pointer"
      title="Change Season"
      style={{ 
        width: '100px', 
        height: '100px',
        background: 'transparent',
        border: 'none',
        outline: 'none'
      }}
    >
      {/* Outer Glow */}
      <div className="absolute inset-[-10px] rounded-full bg-gradient-radial from-blue-400/30 via-cyan-200/15 to-transparent blur-2xl group-hover:from-blue-400/50 transition-all duration-500 pointer-events-none" />
      
      {/* Three.js Canvas */}
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        style={{ 
          width: '100%', 
          height: '100%',
          background: 'transparent'
        }}
      >
        <Earth3D isRotating={isRotating} earthTexture={earthTexture} />
      </Canvas>

      {/* Tooltip on Hover */}
      <div className="absolute -bottom-12 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <span className="text-xs font-medium text-gray-700 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-full shadow-lg whitespace-nowrap">
          Click to change season
        </span>
      </div>
    </button>
  )
}
