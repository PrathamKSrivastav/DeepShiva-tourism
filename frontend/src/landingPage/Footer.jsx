import React from 'react'
import { motion } from 'framer-motion'

export default function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 2.5, duration: 1 }}
      className="fixed bottom-6 left-0 right-0 z-30"
    >
      <div className="text-center">
        <p className="text-sm text-gray-400 font-light tracking-wide">
          Built by team <span className="text-primary-dark font-medium">rasML·AI</span>
        </p>
      </div>
    </motion.footer>
  )
}
