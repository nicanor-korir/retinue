/**
 * Launch Configuration for Deviant/Deviant
 * Official Launch Date: December 22nd, 2025
 */

export const LAUNCH_CONFIG = {
  // Launch date in UTC - December 22, 2025, 00:00:00
  launchDate: new Date('2025-12-22T00:00:00Z'),

  // Early access cutoff (1 minute before launch)
  earlyAccessCutoff: new Date('2025-12-21T23:59:59Z'),

  // Grace period end (7 days after launch - early adopter benefits still available)
  gracePeriodEnd: new Date('2025-12-29T23:59:59Z'),

  // Feature flags
  features: {
    showModal: false,          // Show first-visit modal
    showBanner: true,          // Show countdown banner in hero
    showConfetti: true,        // Show confetti on launch
    showCountdownInCTA: true,  // Show countdown in final CTA section
  },

  // Messaging
  messages: {
    preLaunch: {
      hero: '🚀 LAUNCH DAY:',
      modal: 'The Wait Is Almost Over',
      cta: 'Reserve My Launch Day Access',
    },
    launchDay: {
      hero: '🎉 WE\'RE LIVE!',
      modal: 'Deviant Is Now Live!',
      cta: 'Start Building Now',
    },
    postLaunch: {
      hero: '✨ Now Available',
      modal: 'Join 1000+ Early Adopters',
      cta: 'Get Started Today',
    },
  },

  // Early adopter benefits
  benefits: {
    discount: '50%',
    duration: '6 months',
    extras: [
      'Direct Founder Access',
      'Priority Support',
      'Shape the Product Roadmap',
      'Beta Feature Access',
    ],
  },
} as const

export type LaunchConfig = typeof LAUNCH_CONFIG

/**
 * Helper function to check current launch phase
 */
export function getLaunchPhase(now: Date = new Date()): 'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch' {
  const currentTime = now.getTime()
  const launchTime = LAUNCH_CONFIG.launchDate.getTime()
  const gracePeriodTime = LAUNCH_CONFIG.gracePeriodEnd.getTime()

  if (currentTime < launchTime) {
    return 'pre-launch'
  } else if (currentTime >= launchTime && currentTime < launchTime + 86400000) { // 24 hours
    return 'launch-day'
  } else if (currentTime >= launchTime && currentTime <= gracePeriodTime) {
    return 'grace-period'
  } else {
    return 'post-launch'
  }
}

/**
 * Helper to get time remaining until launch
 */
export function getTimeRemaining(targetDate: Date = LAUNCH_CONFIG.launchDate) {
  const now = new Date()
  const difference = targetDate.getTime() - now.getTime()

  if (difference <= 0) {
    return {
      total: 0,
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      isLaunched: true,
    }
  }

  return {
    total: difference,
    days: Math.floor(difference / (1000 * 60 * 60 * 24)),
    hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
    minutes: Math.floor((difference / 1000 / 60) % 60),
    seconds: Math.floor((difference / 1000) % 60),
    isLaunched: false,
  }
}

/**
 * Progressive urgency levels based on time remaining
 * Returns urgency level from 0 (no urgency) to 3 (critical urgency)
 */
export function getUrgencyLevel(targetDate: Date = LAUNCH_CONFIG.launchDate): 0 | 1 | 2 | 3 {
  const remaining = getTimeRemaining(targetDate)

  if (remaining.isLaunched) return 0

  const daysRemaining = remaining.days

  // Critical: Less than 3 days
  if (daysRemaining < 3) return 3

  // High: Less than 7 days
  if (daysRemaining < 7) return 2

  // Medium: Less than 14 days
  if (daysRemaining < 14) return 1

  // Low: 14+ days
  return 0
}

/**
 * Get animation speed multiplier based on urgency
 * Higher urgency = faster animations
 */
export function getAnimationSpeed(urgencyLevel: 0 | 1 | 2 | 3): number {
  const speeds = {
    0: 1.0,   // Normal speed
    1: 1.2,   // 20% faster
    2: 1.5,   // 50% faster
    3: 2.0,   // 2x faster (double speed)
  }
  return speeds[urgencyLevel]
}

/**
 * Get pulse animation intensity based on urgency
 */
export function getPulseIntensity(urgencyLevel: 0 | 1 | 2 | 3): { min: number; max: number } {
  const intensities = {
    0: { min: 0.95, max: 1.05 },   // Subtle
    1: { min: 0.92, max: 1.08 },   // Noticeable
    2: { min: 0.88, max: 1.12 },   // Strong
    3: { min: 0.85, max: 1.15 },   // Intense
  }
  return intensities[urgencyLevel]
}

/**
 * Get color intensity based on urgency
 * Returns opacity value for overlay effects
 */
export function getColorIntensity(urgencyLevel: 0 | 1 | 2 | 3): number {
  const intensities = {
    0: 0.9,   // 90% opacity
    1: 0.92,  // 92% opacity
    2: 0.95,  // 95% opacity
    3: 1.0,   // 100% opacity (full intensity)
  }
  return intensities[urgencyLevel]
}
