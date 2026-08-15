"use client"

import { useState, useEffect, useCallback } from 'react'
import { LAUNCH_CONFIG, getTimeRemaining, getLaunchPhase, getUrgencyLevel } from './launchConfig'

export interface CountdownTime {
  days: number
  hours: number
  minutes: number
  seconds: number
  total: number
  isLaunched: boolean
}

export interface UseLaunchCountdownReturn {
  timeRemaining: CountdownTime
  launchPhase: 'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch'
  formattedLaunchDate: string
  isCountdownActive: boolean
  urgencyLevel: 0 | 1 | 2 | 3
}

/**
 * Custom hook to manage launch countdown with real-time updates
 * Handles timezone conversion and automatic updates every second
 */
export function useLaunchCountdown(): UseLaunchCountdownReturn {
  const [timeRemaining, setTimeRemaining] = useState<CountdownTime>(() =>
    getTimeRemaining(LAUNCH_CONFIG.launchDate)
  )
  const [launchPhase, setLaunchPhase] = useState<'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch'>(() =>
    getLaunchPhase()
  )
  const [urgencyLevel, setUrgencyLevel] = useState<0 | 1 | 2 | 3>(() =>
    getUrgencyLevel(LAUNCH_CONFIG.launchDate)
  )

  // Format launch date for display in user's timezone
  const formattedLaunchDate = new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(LAUNCH_CONFIG.launchDate)

  // Update countdown every second
  const updateCountdown = useCallback(() => {
    const remaining = getTimeRemaining(LAUNCH_CONFIG.launchDate)
    setTimeRemaining(remaining)

    // Update phase if it changed
    const currentPhase = getLaunchPhase()
    if (currentPhase !== launchPhase) {
      setLaunchPhase(currentPhase)
    }

    // Update urgency level
    const currentUrgency = getUrgencyLevel(LAUNCH_CONFIG.launchDate)
    if (currentUrgency !== urgencyLevel) {
      setUrgencyLevel(currentUrgency)
    }

    // Trigger celebration when countdown reaches zero
    if (remaining.isLaunched && remaining.total === 0) {
      // Store launch celebration trigger in sessionStorage
      if (typeof window !== 'undefined' && !sessionStorage.getItem('launch-celebrated')) {
        sessionStorage.setItem('launch-celebrated', 'true')
        // Dispatch custom event for celebration
        window.dispatchEvent(new CustomEvent('launch-celebration'))
      }
    }
  }, [launchPhase, urgencyLevel])

  useEffect(() => {
    // Initial update
    updateCountdown()

    // Set up interval for updates
    const intervalId = setInterval(updateCountdown, 1000)

    // Cleanup
    return () => {
      clearInterval(intervalId)
    }
  }, [updateCountdown])

  const isCountdownActive = launchPhase === 'pre-launch' && !timeRemaining.isLaunched

  return {
    timeRemaining,
    launchPhase,
    formattedLaunchDate,
    isCountdownActive,
    urgencyLevel,
  }
}

/**
 * Hook to manage first-visit modal state
 */
export function useFirstVisitModal() {
  const [showModal, setShowModal] = useState(false)
  const [hasShown, setHasShown] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return

    // Check if modal has been shown before
    const modalDismissed = localStorage.getItem('launch-modal-dismissed')
    const launchPhase = getLaunchPhase()

    // Only show modal in pre-launch phase and if not previously dismissed
    if (!modalDismissed && launchPhase === 'pre-launch' && !hasShown && LAUNCH_CONFIG.features.showModal) {
      // Show modal after 2 seconds
      const timeoutId = setTimeout(() => {
        setShowModal(true)
        setHasShown(true)
      }, 2000)

      return () => clearTimeout(timeoutId)
    }
  }, [hasShown])

  const dismissModal = useCallback(() => {
    setShowModal(false)
    if (typeof window !== 'undefined') {
      localStorage.setItem('launch-modal-dismissed', 'true')
    }
  }, [])

  return {
    showModal,
    dismissModal,
  }
}

/**
 * Format a number with leading zero if needed
 */
export function formatTimeUnit(value: number): string {
  return value.toString().padStart(2, '0')
}
