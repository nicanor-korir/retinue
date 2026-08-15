# Launch Countdown Configuration Reference

Complete reference for all configuration options, feature flags, and customization points.

## 📋 Table of Contents

- [Launch Config](#launch-config)
- [Feature Flags](#feature-flags)
- [Messages](#messages)
- [Benefits](#benefits)
- [Urgency System](#urgency-system)
- [Component Props](#component-props)
- [Hook API](#hook-api)
- [Utility Functions](#utility-functions)

---

## Launch Config

File: `components/launch/launchConfig.ts`

### Core Configuration

```typescript
export const LAUNCH_CONFIG = {
  // Launch date in UTC (Required)
  launchDate: Date

  // Early access cutoff date (Optional)
  earlyAccessCutoff: Date

  // Grace period end date (Optional)
  gracePeriodEnd: Date

  // Feature toggles (Required)
  features: FeatureFlags

  // Phase-specific messaging (Required)
  messages: Messages

  // Early adopter benefits (Required)
  benefits: Benefits
}
```

### Example

```typescript
export const LAUNCH_CONFIG = {
  launchDate: new Date('2025-12-22T00:00:00Z'),
  earlyAccessCutoff: new Date('2025-12-21T23:59:59Z'),
  gracePeriodEnd: new Date('2025-12-29T23:59:59Z'),

  features: { /* ... */ },
  messages: { /* ... */ },
  benefits: { /* ... */ },
} as const
```

---

## Feature Flags

Control which features are enabled/disabled.

### Interface

```typescript
interface FeatureFlags {
  showModal: boolean           // First-visit modal
  showBanner: boolean          // Hero countdown banner
  showConfetti: boolean        // Launch celebration
  enableReminders: boolean     // Email reminder system
  showCountdownInCTA: boolean  // CTA section countdown
}
```

### Default Values

```typescript
features: {
  showModal: true,
  showBanner: true,
  showConfetti: true,
  enableReminders: true,
  showCountdownInCTA: true,
}
```

### Usage Examples

#### Disable Everything Except Banner

```typescript
features: {
  showModal: false,
  showBanner: true,
  showConfetti: false,
  enableReminders: false,
  showCountdownInCTA: false,
}
```

#### Post-Launch: Disable All Countdown Features

```typescript
features: {
  showModal: false,
  showBanner: false,
  showConfetti: false,
  enableReminders: false,
  showCountdownInCTA: false,
}
```

---

## Messages

Phase-specific messaging for different components.

### Interface

```typescript
interface Messages {
  preLaunch: PhaseMessages
  launchDay: PhaseMessages
  postLaunch: PhaseMessages
}

interface PhaseMessages {
  hero: string   // Hero section banner text
  modal: string  // Modal headline
  cta: string    // Call-to-action button text
}
```

### Default Values

```typescript
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
}
```

### Customization Examples

#### Urgent/Aggressive Messaging

```typescript
messages: {
  preLaunch: {
    hero: '⚡ LAUNCHING IN:',
    modal: 'Don't Miss Out - Reserve Your Spot',
    cta: 'Claim Early Access NOW',
  },
  launchDay: {
    hero: '🔥 LIVE NOW - GET 50% OFF!',
    modal: 'Limited Time Launch Offer',
    cta: 'Get Started - 50% Off Today Only',
  },
}
```

#### Calm/Professional Messaging

```typescript
messages: {
  preLaunch: {
    hero: 'Coming Soon:',
    modal: 'Thank You for Your Interest',
    cta: 'Request Early Access',
  },
  launchDay: {
    hero: 'Now Available',
    modal: 'Welcome to Deviant',
    cta: 'Get Started',
  },
}
```

---

## Benefits

Early adopter benefits displayed in modal and banners.

### Interface

```typescript
interface Benefits {
  discount: string       // Discount percentage
  duration: string       // Discount duration
  extras: string[]       // Additional benefits list
}
```

### Default Values

```typescript
benefits: {
  discount: '50%',
  duration: '6 months',
  extras: [
    'Direct Founder Access',
    'Priority Support',
    'Shape the Product Roadmap',
    'Beta Feature Access',
  ],
}
```

### Customization Examples

#### Lifetime Deal

```typescript
benefits: {
  discount: '70%',
  duration: 'lifetime',
  extras: [
    'Lifetime Updates',
    'Premium Support Forever',
    'Early Access to All Features',
    'VIP Slack Channel Access',
  ],
}
```

#### Simple Discount

```typescript
benefits: {
  discount: '30%',
  duration: '3 months',
  extras: [
    'Priority Support',
    'Early Access',
  ],
}
```

---

## Urgency System

Progressive urgency increases as launch approaches.

### Urgency Levels

| Level | Days Remaining | Speed | Pulse | Color | Behavior |
|-------|----------------|-------|-------|-------|----------|
| 0 | 14+ days | 1.0x | Subtle | 90% | Calm |
| 1 | 7-14 days | 1.2x | Noticeable | 92% | Building |
| 2 | 3-7 days | 1.5x | Strong | 95% | Urgent |
| 3 | <3 days | 2.0x | Intense | 100% | Critical |

### Configuration

```typescript
// components/launch/launchConfig.ts

export function getUrgencyLevel(targetDate: Date): 0 | 1 | 2 | 3 {
  const remaining = getTimeRemaining(targetDate)
  const daysRemaining = remaining.days

  if (daysRemaining < 3) return 3    // Critical
  if (daysRemaining < 7) return 2    // High
  if (daysRemaining < 14) return 1   // Medium
  return 0                            // Low
}
```

### Customization Examples

#### More Aggressive (Earlier Urgency)

```typescript
export function getUrgencyLevel(targetDate: Date): 0 | 1 | 2 | 3 {
  const daysRemaining = getTimeRemaining(targetDate).days

  if (daysRemaining < 5) return 3    // Last 5 days
  if (daysRemaining < 14) return 2   // Last 2 weeks
  if (daysRemaining < 30) return 1   // Last month
  return 0
}
```

#### Final Hours Only

```typescript
export function getUrgencyLevel(targetDate: Date): 0 | 1 | 2 | 3 {
  const remaining = getTimeRemaining(targetDate)

  if (remaining.days === 0 && remaining.hours < 6) return 3   // Last 6 hours
  if (remaining.days === 0 && remaining.hours < 24) return 2  // Last 24 hours
  if (remaining.days < 3) return 1                             // Last 3 days
  return 0
}
```

### Animation Speed

```typescript
export function getAnimationSpeed(urgencyLevel: 0 | 1 | 2 | 3): number {
  const speeds = {
    0: 1.0,   // Normal
    1: 1.2,   // 20% faster
    2: 1.5,   // 50% faster
    3: 2.0,   // 2x faster
  }
  return speeds[urgencyLevel]
}

// Custom speeds
const speeds = {
  0: 1.0,
  1: 1.5,   // 50% faster
  2: 2.0,   // 2x faster
  3: 3.0,   // 3x faster (very intense)
}
```

### Pulse Intensity

```typescript
export function getPulseIntensity(urgencyLevel: 0 | 1 | 2 | 3) {
  const intensities = {
    0: { min: 0.95, max: 1.05 },   // Subtle
    1: { min: 0.92, max: 1.08 },   // Noticeable
    2: { min: 0.88, max: 1.12 },   // Strong
    3: { min: 0.85, max: 1.15 },   // Intense
  }
  return intensities[urgencyLevel]
}

// Custom intensities (more dramatic)
const intensities = {
  0: { min: 0.98, max: 1.02 },   // Very subtle
  1: { min: 0.90, max: 1.10 },   // Moderate
  2: { min: 0.80, max: 1.20 },   // Dramatic
  3: { min: 0.70, max: 1.30 },   // Extreme
}
```

---

## Component Props

### LaunchCountdown

```typescript
interface LaunchCountdownProps {
  variant?: 'default' | 'compact' | 'banner'
  className?: string
}

// Usage
<LaunchCountdown />
<LaunchCountdown variant="compact" />
<LaunchCountdown variant="banner" className="my-8" />
```

### LaunchBanner

```typescript
interface LaunchBannerProps {
  onCTAClick?: () => void
  className?: string
}

// Usage
<LaunchBanner />
<LaunchBanner onCTAClick={() => alert('CTA clicked')} />
<LaunchBanner className="mb-12" />
```

### LaunchModal

```typescript
interface LaunchModalProps {
  onJoinWaitlist?: () => void
}

// Usage
<LaunchModal />
<LaunchModal onJoinWaitlist={() => scrollToForm()} />
```

### LaunchCelebration

```typescript
// No props - fully automatic
<LaunchCelebration />

// Manual trigger
import { triggerLaunchCelebration } from '@/components/launch'
<button onClick={triggerLaunchCelebration}>Celebrate</button>
```

### CompactCountdown

```typescript
interface CompactCountdownProps {
  className?: string
}

// Usage
<CompactCountdown />
<CompactCountdown className="font-bold text-primary" />
```

---

## Hook API

### useLaunchCountdown()

```typescript
const {
  timeRemaining,      // CountdownTime object
  launchPhase,        // 'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch'
  formattedLaunchDate,// Formatted date string
  isCountdownActive,  // boolean
  urgencyLevel,       // 0 | 1 | 2 | 3
} = useLaunchCountdown()
```

#### CountdownTime Interface

```typescript
interface CountdownTime {
  days: number
  hours: number
  minutes: number
  seconds: number
  total: number        // Total milliseconds remaining
  isLaunched: boolean
}
```

#### Example

```typescript
function MyComponent() {
  const { timeRemaining, launchPhase, urgencyLevel } = useLaunchCountdown()

  return (
    <div>
      <p>Days: {timeRemaining.days}</p>
      <p>Phase: {launchPhase}</p>
      <p>Urgency: {urgencyLevel}</p>
    </div>
  )
}
```

### useFirstVisitModal()

```typescript
const {
  showModal,    // boolean
  dismissModal, // () => void
} = useFirstVisitModal()
```

#### Example

```typescript
function MyModal() {
  const { showModal, dismissModal } = useFirstVisitModal()

  if (!showModal) return null

  return (
    <div>
      <button onClick={dismissModal}>Close</button>
      <p>Modal content</p>
    </div>
  )
}
```

---

## Utility Functions

### getLaunchPhase()

```typescript
function getLaunchPhase(now?: Date): 'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch'

// Usage
const phase = getLaunchPhase()
const futurePhase = getLaunchPhase(new Date('2025-12-25'))
```

### getTimeRemaining()

```typescript
function getTimeRemaining(targetDate?: Date): CountdownTime

// Usage
const remaining = getTimeRemaining()
const customRemaining = getTimeRemaining(new Date('2026-01-01'))
```

### getUrgencyLevel()

```typescript
function getUrgencyLevel(targetDate?: Date): 0 | 1 | 2 | 3

// Usage
const urgency = getUrgencyLevel()
```

### getAnimationSpeed()

```typescript
function getAnimationSpeed(urgencyLevel: 0 | 1 | 2 | 3): number

// Usage
const speed = getAnimationSpeed(3)  // Returns 2.0
```

### getPulseIntensity()

```typescript
function getPulseIntensity(urgencyLevel: 0 | 1 | 2 | 3): { min: number; max: number }

// Usage
const { min, max } = getPulseIntensity(2)
```

### getColorIntensity()

```typescript
function getColorIntensity(urgencyLevel: 0 | 1 | 2 | 3): number

// Usage
const opacity = getColorIntensity(1)  // Returns 0.92
```

### formatTimeUnit()

```typescript
function formatTimeUnit(value: number): string

// Usage
formatTimeUnit(5)   // Returns "05"
formatTimeUnit(15)  // Returns "15"
```

### triggerLaunchCelebration()

```typescript
function triggerLaunchCelebration(): void

// Usage
<button onClick={triggerLaunchCelebration}>
  Test Celebration
</button>
```

---

## API Endpoints

### POST /api/launch-reminder

Email reminder signup.

**Request:**
```typescript
{
  email: string  // Required, must be valid email
}
```

**Response (Success):**
```typescript
{
  success: true,
  message: "You'll receive a reminder on launch day!"
}
```

**Response (Error):**
```typescript
{
  success: false,
  message: string,
  errors?: ZodIssue[]
}
```

**Example:**
```typescript
const response = await fetch('/api/launch-reminder', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' }),
})

const data = await response.json()

if (data.success) {
  console.log('Reminder set!')
} else {
  console.error('Error:', data.message)
}
```

---

## Environment Variables

### Optional (for production integration)

```bash
# .env.local

# Email service API key (SendGrid, Mailchimp, etc.)
EMAIL_SERVICE_API_KEY=your_api_key_here

# Database connection (for storing reminders)
DATABASE_URL=your_database_url

# Analytics tracking
ANALYTICS_ID=your_analytics_id
```

---

## TypeScript Types

### Exported Types

```typescript
// Import from components/launch
import type {
  LaunchConfig,
  CountdownTime,
  UseLaunchCountdownReturn,
} from '@/components/launch'
```

### Type Definitions

```typescript
type LaunchConfig = typeof LAUNCH_CONFIG

interface CountdownTime {
  days: number
  hours: number
  minutes: number
  seconds: number
  total: number
  isLaunched: boolean
}

interface UseLaunchCountdownReturn {
  timeRemaining: CountdownTime
  launchPhase: 'pre-launch' | 'launch-day' | 'grace-period' | 'post-launch'
  formattedLaunchDate: string
  isCountdownActive: boolean
  urgencyLevel: 0 | 1 | 2 | 3
}
```

---

## Quick Reference

### Common Configuration Changes

| What to Change | File | Line(s) |
|----------------|------|---------|
| Launch date | `launchConfig.ts` | 8 |
| Enable/disable features | `launchConfig.ts` | 17-23 |
| Hero text | `launchConfig.ts` | 28 |
| Modal headline | `launchConfig.ts` | 29 |
| CTA button text | `launchConfig.ts` | 30 |
| Discount amount | `launchConfig.ts` | 46 |
| Discount duration | `launchConfig.ts` | 47 |
| Benefits list | `launchConfig.ts` | 48-53 |
| Urgency thresholds | `launchConfig.ts` | 110-128 |
| Modal delay | `useLaunchCountdown.ts` | ~106 |
| Confetti colors | `LaunchCelebration.tsx` | ~49 |

---

**Last Updated:** November 2025
