/**
 * Launch Components - Deviant/Deviant Launch Countdown
 * Export all launch-related components, hooks, and utilities
 */

export { LaunchCountdown, CompactCountdown } from './LaunchCountdown'
export { LaunchBanner } from './LaunchBanner'
export { LaunchModal } from './LaunchModal'
export { LaunchCelebration, triggerLaunchCelebration } from './LaunchCelebration'
export { useLaunchCountdown, useFirstVisitModal, formatTimeUnit } from './useLaunchCountdown'
export {
  LAUNCH_CONFIG,
  getLaunchPhase,
  getTimeRemaining,
  getUrgencyLevel,
  getAnimationSpeed,
  getPulseIntensity,
  getColorIntensity,
} from './launchConfig'
export type { LaunchConfig } from './launchConfig'
export type { CountdownTime, UseLaunchCountdownReturn } from './useLaunchCountdown'
