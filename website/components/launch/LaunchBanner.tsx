"use client"

import { motion } from "framer-motion"
import { Rocket, Sparkles, ArrowRight } from "lucide-react"
import { LaunchCountdown } from "./LaunchCountdown"
import { useLaunchCountdown } from "./useLaunchCountdown"
import { LAUNCH_CONFIG } from "./launchConfig"

interface LaunchBannerProps {
  onCTAClick?: () => void
  className?: string
}

/**
 * Launch banner to display at the top of hero section
 * Shows countdown and creates urgency for launch day
 */
export function LaunchBanner({ onCTAClick, className = '' }: LaunchBannerProps) {
  const { launchPhase, isCountdownActive, formattedLaunchDate } = useLaunchCountdown()

  // Don't show banner if features are disabled
  if (!LAUNCH_CONFIG.features.showBanner) {
    return null
  }

  // Pre-launch banner with countdown
  if (launchPhase === 'pre-launch' && isCountdownActive) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className={`relative overflow-hidden rounded-2xl ${className}`}
      >
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--primary)] via-[var(--accent)] to-[var(--secondary)] opacity-95" />

        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }} />
        </div>

        {/* Content */}
        <div className="relative z-10 px-6 py-8 md:px-12 md:py-10">
          {/* Header */}
          <div className="text-center mb-6">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="inline-flex items-center gap-2 mb-3"
            >
              <Rocket className="w-6 h-6 text-white" />
              <h3 className="text-xl sm:text-2xl md:text-3xl font-bold text-white font-['Poppins']">
                {LAUNCH_CONFIG.messages.preLaunch.hero}
              </h3>
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>

            <p className="text-white/90 text-sm sm:text-base md:text-lg">
              <span className="font-semibold">December 22nd, 2025</span> • Be among the first 1000 to access autonomous AI development
            </p>
          </div>

          {/* Countdown */}
          <div className="mb-6">
            <LaunchCountdown variant="banner" />
          </div>

          {/* Benefits strip */}
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-xs sm:text-sm text-white/90">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span className="font-medium">50% Off for 6 Months</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse delay-300" />
              <span className="font-medium">Direct Founder Access</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse delay-700" />
              <span className="font-medium">Priority Support</span>
            </div>
          </div>

          {/* CTA Button */}
          {onCTAClick && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="mt-6 flex justify-center"
            >
              <button
                onClick={onCTAClick}
                className="group inline-flex items-center gap-2 px-8 py-3 bg-white text-[var(--primary)] rounded-full font-bold text-sm sm:text-base shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
              >
                {LAUNCH_CONFIG.messages.preLaunch.cta}
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>
          )}
        </div>

        {/* Decorative elements */}
        <motion.div
          animate={{
            rotate: [0, 360],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute -top-20 -right-20 w-40 h-40 bg-white/10 rounded-full blur-2xl"
        />
        <motion.div
          animate={{
            rotate: [360, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute -bottom-20 -left-20 w-40 h-40 bg-white/10 rounded-full blur-2xl"
        />
      </motion.div>
    )
  }

  // Launch day celebration banner
  if (launchPhase === 'launch-day') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className={`relative overflow-hidden rounded-2xl ${className}`}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--secondary)] via-[var(--accent)] to-[var(--primary)] opacity-95" />

        <div className="relative z-10 px-6 py-8 md:px-12 md:py-10 text-center">
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            <h3 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white font-['Poppins'] mb-3">
              {LAUNCH_CONFIG.messages.launchDay.hero}
            </h3>
          </motion.div>

          <p className="text-white/90 text-lg sm:text-xl md:text-2xl mb-6">
            Retinue Is Now Available • Start Building Your AI Company Today
          </p>

          {onCTAClick && (
            <button
              onClick={onCTAClick}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-white text-[var(--primary)] rounded-full font-bold text-base sm:text-lg shadow-2xl hover:shadow-3xl hover:scale-105 transition-all duration-200"
            >
              {LAUNCH_CONFIG.messages.launchDay.cta}
              <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
            </button>
          )}
        </div>
      </motion.div>
    )
  }

  // Grace period banner (early adopter benefits still available)
  if (launchPhase === 'grace-period') {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative overflow-hidden rounded-2xl ${className}`}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] opacity-90" />

        <div className="relative z-10 px-6 py-4 md:px-8 md:py-6 text-center">
          <p className="text-white text-sm sm:text-base md:text-lg">
            <span className="font-bold">⚡ Limited Time:</span> Early adopter benefits end in{' '}
            {Math.ceil((LAUNCH_CONFIG.gracePeriodEnd.getTime() - Date.now()) / (1000 * 60 * 60 * 24))} days
            <span className="mx-2">•</span>
            <span className="font-semibold">Get 50% off for 6 months</span>
          </p>
        </div>
      </motion.div>
    )
  }

  // Post-launch: don't show banner
  return null
}
