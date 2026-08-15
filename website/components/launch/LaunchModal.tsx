"use client"

import { motion, AnimatePresence } from "framer-motion"
import { X, Rocket, ArrowRight, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { LaunchCountdown } from "./LaunchCountdown"
import { useFirstVisitModal, useLaunchCountdown } from "./useLaunchCountdown"
import { LAUNCH_CONFIG } from "./launchConfig"

interface LaunchModalProps {
  onJoinWaitlist?: () => void
}

/**
 * First-visit modal that appears 2 seconds after page load
 * Shows countdown and early adopter benefits
 */
export function LaunchModal({ onJoinWaitlist }: LaunchModalProps) {
  const { showModal, dismissModal } = useFirstVisitModal()
  const { isCountdownActive, formattedLaunchDate } = useLaunchCountdown()

  // Only show modal if countdown is active
  if (!isCountdownActive || !showModal) {
    return null
  }

  const handleJoinWaitlist = () => {
    dismissModal()
    if (onJoinWaitlist) {
      onJoinWaitlist()
    }
  }

  return (
    <AnimatePresence>
      {showModal && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={dismissModal}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="relative max-w-2xl w-full"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close button */}
              <button
                onClick={dismissModal}
                className="absolute -top-3 -right-3 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-100 transition-colors z-10"
                aria-label="Close modal"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>

              {/* Modal content */}
              <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
                {/* Header with gradient */}
                <div className="relative bg-gradient-to-r from-[var(--primary)] via-[var(--accent)] to-[var(--secondary)] p-8 pb-6">
                  {/* Background pattern */}
                  <div className="absolute inset-0 opacity-10">
                    <div
                      className="absolute inset-0"
                      style={{
                        backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
                        backgroundSize: '40px 40px',
                      }}
                    />
                  </div>

                  {/* Floating particles */}
                  <div className="absolute inset-0 overflow-hidden">
                    {[...Array(8)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute w-1 h-1 bg-white/40 rounded-full"
                        style={{
                          left: `${Math.random() * 100}%`,
                          top: `${Math.random() * 100}%`,
                        }}
                        animate={{
                          y: [0, -20, 0],
                          opacity: [0.4, 0.8, 0.4],
                        }}
                        transition={{
                          duration: 2 + Math.random(),
                          repeat: Infinity,
                          delay: Math.random(),
                        }}
                      />
                    ))}
                  </div>

                  <div className="relative z-10">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.2, type: "spring" }}
                      className="flex justify-center mb-4"
                    >
                      <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                        <Rocket className="w-8 h-8 text-white" />
                      </div>
                    </motion.div>

                    <h2 className="text-3xl sm:text-4xl font-bold text-white text-center mb-3 font-['Poppins']">
                      {LAUNCH_CONFIG.messages.preLaunch.modal}
                    </h2>

                    <p className="text-white/90 text-center text-base sm:text-lg">
                      Deviant launches on <span className="font-bold">{formattedLaunchDate}</span>
                    </p>
                  </div>
                </div>

                {/* Countdown section */}
                <div className="bg-gradient-to-b from-gray-50 to-white px-8 py-6">
                  <LaunchCountdown />
                </div>

                {/* Content section */}
                <div className="px-8 py-6">
                  {/* Benefits */}
                  <div className="mb-6">
                    <h3 className="text-xl font-bold text-[var(--heading)] mb-4 flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-[var(--accent)]" />
                      Early Adopter Benefits
                    </h3>
                    <ul className="space-y-2 text-[var(--body)]">
                      {LAUNCH_CONFIG.benefits.extras.map((benefit, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <div className="w-1.5 h-1.5 bg-[var(--primary)] rounded-full mt-2 flex-shrink-0" />
                          <span>{benefit}</span>
                        </li>
                      ))}
                      <li className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-[var(--secondary)] rounded-full mt-2 flex-shrink-0" />
                        <span className="font-semibold">
                          {LAUNCH_CONFIG.benefits.discount} Off for {LAUNCH_CONFIG.benefits.duration}
                        </span>
                      </li>
                    </ul>
                  </div>

                  {/* Primary CTA */}
                  <Button
                    onClick={handleJoinWaitlist}
                    size="lg"
                    className="w-full group"
                  >
                    {LAUNCH_CONFIG.messages.preLaunch.cta}
                    <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </Button>

                  {/* Dismiss link */}
                  <button
                    onClick={dismissModal}
                    className="w-full mt-4 text-sm text-[var(--muted)] hover:text-[var(--body)] transition-colors"
                  >
                    Continue exploring
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
