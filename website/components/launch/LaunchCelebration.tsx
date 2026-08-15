"use client"

import { useEffect } from "react"
import confetti from "canvas-confetti"
import { LAUNCH_CONFIG } from "./launchConfig"

/**
 * Launch celebration component
 * Listens for launch-celebration event and triggers confetti animation
 */
export function LaunchCelebration() {
  useEffect(() => {
    if (!LAUNCH_CONFIG.features.showConfetti) return

    const handleLaunchCelebration = () => {
      // Fire confetti from multiple angles for dramatic effect
      const duration = 3000
      const animationEnd = Date.now() + duration
      const defaults = {
        startVelocity: 30,
        spread: 360,
        ticks: 60,
        zIndex: 9999,
      }

      function randomInRange(min: number, max: number) {
        return Math.random() * (max - min) + min
      }

      // Continuous confetti burst
      const interval = setInterval(() => {
        const timeLeft = animationEnd - Date.now()

        if (timeLeft <= 0) {
          return clearInterval(interval)
        }

        const particleCount = 50 * (timeLeft / duration)

        // Fire from left side
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
          colors: ['#0066FF', '#8B5CF6', '#FF6B35'],
        })

        // Fire from right side
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
          colors: ['#0066FF', '#8B5CF6', '#FF6B35'],
        })
      }, 250)

      // Big burst in the center after 500ms
      setTimeout(() => {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#0066FF', '#8B5CF6', '#FF6B35'],
          zIndex: 9999,
        })
      }, 500)

      // Fireworks effect
      setTimeout(() => {
        const count = 200
        const confettiDefaults = {
          origin: { y: 0.7 },
          zIndex: 9999,
        }

        function fire(particleRatio: number, opts: confetti.Options) {
          confetti({
            ...confettiDefaults,
            ...opts,
            particleCount: Math.floor(count * particleRatio),
            colors: ['#0066FF', '#8B5CF6', '#FF6B35'],
          })
        }

        fire(0.25, {
          spread: 26,
          startVelocity: 55,
        })

        fire(0.2, {
          spread: 60,
        })

        fire(0.35, {
          spread: 100,
          decay: 0.91,
          scalar: 0.8,
        })

        fire(0.1, {
          spread: 120,
          startVelocity: 25,
          decay: 0.92,
          scalar: 1.2,
        })

        fire(0.1, {
          spread: 120,
          startVelocity: 45,
        })
      }, 1500)
    }

    // Listen for launch celebration event
    window.addEventListener('launch-celebration', handleLaunchCelebration)

    return () => {
      window.removeEventListener('launch-celebration', handleLaunchCelebration)
    }
  }, [])

  // This component doesn't render anything
  return null
}

/**
 * Manually trigger confetti celebration
 * Can be used for testing or manual triggers
 */
export function triggerLaunchCelebration() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('launch-celebration'))
  }
}
