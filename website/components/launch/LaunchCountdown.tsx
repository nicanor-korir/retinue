"use client"

import { motion, AnimatePresence } from "framer-motion"
import { useLaunchCountdown, formatTimeUnit } from "./useLaunchCountdown"
import { LAUNCH_CONFIG } from "./launchConfig"

interface CountdownUnitProps {
  value: number
  label: string
  previousValue?: number
}

/**
 * Individual countdown unit with flip animation
 */
function CountdownUnit({ value, label, previousValue }: CountdownUnitProps) {
  const formattedValue = formatTimeUnit(value)
  const shouldAnimate = previousValue !== undefined && previousValue !== value

  return (
    <div className="flex flex-col items-center">
      {/* Number display with flip animation */}
      <div className="relative w-16 h-20 sm:w-20 sm:h-24 md:w-24 md:h-28 mb-2 perspective-1000">
        <AnimatePresence mode="wait">
          <motion.div
            key={formattedValue}
            initial={shouldAnimate ? { rotateX: -90, opacity: 0 } : false}
            animate={{ rotateX: 0, opacity: 1 }}
            exit={{ rotateX: 90, opacity: 0 }}
            transition={{
              duration: 0.6,
              ease: "easeInOut",
            }}
            className="absolute inset-0 bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] rounded-lg shadow-2xl flex items-center justify-center border-2 border-white/20 backdrop-blur-sm"
          >
            <span className="text-3xl sm:text-4xl md:text-5xl font-bold text-white font-['Poppins']">
              {formattedValue}
            </span>
          </motion.div>
        </AnimatePresence>

        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] rounded-lg blur-xl opacity-30 animate-pulse" />
      </div>

      {/* Label */}
      <span className="text-xs sm:text-sm md:text-base font-medium text-[var(--heading)] uppercase tracking-wider">
        {label}
      </span>
    </div>
  )
}

interface LaunchCountdownProps {
  variant?: 'default' | 'compact' | 'banner'
  className?: string
}

/**
 * Launch countdown component with real-time updates and animations
 */
export function LaunchCountdown({ variant = 'default', className = '' }: LaunchCountdownProps) {
  const { timeRemaining, launchPhase, isCountdownActive } = useLaunchCountdown()

  // If countdown is not active, don't render
  if (!isCountdownActive) {
    return null
  }

  const isCompact = variant === 'compact' || variant === 'banner'

  return (
    <div className={`relative ${className}`}>
      {/* Countdown units */}
      <div className={`flex gap-3 sm:gap-4 md:gap-6 ${isCompact ? 'justify-center' : 'justify-center'}`}>
        <CountdownUnit
          value={timeRemaining.days}
          label="Days"
        />

        {/* Separator */}
        <div className="flex items-center justify-center pb-8">
          <span className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--muted)]">:</span>
        </div>

        <CountdownUnit
          value={timeRemaining.hours}
          label="Hours"
        />

        {/* Separator */}
        <div className="flex items-center justify-center pb-8">
          <span className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--muted)]">:</span>
        </div>

        <CountdownUnit
          value={timeRemaining.minutes}
          label="Minutes"
        />

        {/* Separator */}
        <div className="flex items-center justify-center pb-8">
          <span className="text-2xl sm:text-3xl md:text-4xl font-bold text-[var(--muted)]">:</span>
        </div>

        <CountdownUnit
          value={timeRemaining.seconds}
          label="Seconds"
        />
      </div>

      {/* Floating particles background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
        {[...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-[var(--primary)]/20 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -30, 0],
              opacity: [0.3, 0.8, 0.3],
              scale: [1, 1.5, 1],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </div>
  )
}

/**
 * Compact countdown for inline use
 */
export function CompactCountdown({ className = '' }: { className?: string }) {
  const { timeRemaining, isCountdownActive } = useLaunchCountdown()

  if (!isCountdownActive) {
    return null
  }

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <span className="font-bold text-lg">
        {timeRemaining.days}d {formatTimeUnit(timeRemaining.hours)}h{' '}
        {formatTimeUnit(timeRemaining.minutes)}m {formatTimeUnit(timeRemaining.seconds)}s
      </span>
    </div>
  )
}
