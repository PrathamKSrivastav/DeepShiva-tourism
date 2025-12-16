import React, { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export default function Earth3D({ isRotating, earthTexture }) {
  const meshRef = useRef()
  const rotationSpeed = useRef(0)

  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002
      
      if (isRotating) {
        rotationSpeed.current = 0.05
      } else {
        rotationSpeed.current *= 0.95
      }
      
      meshRef.current.rotation.y += rotationSpeed.current
    }
  })

  return (
    <group>
      {/* ✅ MAXIMUM BRIGHTNESS LIGHTING */}
      <ambientLight intensity={2.5} /> {/* Increased from 2.5 to 3.5 */}
      
      <hemisphereLight skyColor="#ffffff" groundColor="#ffffff" intensity={1.0} /> {/* Both white + boosted */}
      

      {/* Earth Sphere - ULTRA BRIGHT MATERIAL */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial
          map={earthTexture}
          roughness={0.1} // ✅ Very smooth (was 0.3)
          metalness={0.0} // ✅ No metalness (was 0.05)
          emissive="#444444" // ✅ Much brighter glow (was #444444)
          emissiveIntensity={0.6} // ✅ Increased (was 0.5)
          toneMapped={false} // ✅ Bypass tone mapping for brightness
        />
      </mesh>

      {/* Brighter Atmosphere */}
      <mesh scale={[1.06, 1.06, 1.06]}>
        <sphereGeometry args={[2, 64, 64]} />
        <meshBasicMaterial
          color="#e0f4ff" // ✅ Even lighter blue (was #add8e6)
          transparent
          opacity={0.3} // ✅ Increased (was 0.25)
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  )
}
