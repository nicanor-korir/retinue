# Launch Countdown System

Comprehensive launch countdown system for Deviant/Deviant's December 22nd, 2025 launch. Features real-time countdown, progressive urgency, first-visit modal, email reminders, and celebration effects.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Components](#components)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Endpoints](#api-endpoints)
- [Customization](#customization)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

---

## Overview

The launch countdown system creates anticipation and drives conversions for the product launch through:

- **Real-time countdown** with animated digits
- **Progressive urgency** that intensifies as launch approaches
- **First-visit modal** to capture early interest
- **Email reminders** for launch day notifications
- **Confetti celebration** when countdown reaches zero
- **Multi-phase support** (pre-launch, launch-day, grace-period, post-launch)

**Launch Date:** December 22nd, 2025, 00:00:00 UTC

---

## Features

### Phase 1: Core Countdown System ✅

- **LaunchCountdown**: Animated countdown component with flip digits
- **LaunchBanner**: Prominent hero section banner with countdown
- **Real-time updates**: Countdown updates every second
- **Timezone handling**: Automatic conversion for all users
- **Responsive design**: Works on mobile and desktop
- **Accessibility**: Screen reader compatible, keyboard navigable

### Phase 2: Enhanced Experience ✅

- **LaunchModal**: First-visit modal with countdown and email capture
- **Email reminders**: API endpoint for launch day notifications
- **Progressive urgency**: Dynamic intensity based on time remaining
- **Confetti celebration**: Automatic celebration on launch day
- **Event system**: Extensible event-driven architecture

---

## Installation

### Dependencies

```bash
npm install canvas-confetti
npm install --save-dev @types/canvas-confetti
```

### File Structure

```
components/launch/
├── LaunchBanner.tsx          # Hero section banner
├── LaunchCountdown.tsx       # Countdown display component
├── LaunchModal.tsx           # First-visit modal
├── LaunchCelebration.tsx     # Confetti celebration
├── launchConfig.ts           # Configuration and utilities
├── useLaunchCountdown.ts     # Countdown hook
├── index.ts                  # Exports
└── README.md                 # This file

app/api/
└── launch-reminder/
    └── route.ts              # Email reminder endpoint
```

---

## Components

### LaunchCountdown

Main countdown component with animated flip digits.

**Props:**
```typescript
interface LaunchCountdownProps {
  variant?: 'default' | 'compact' | 'banner'
  className?: string
}
```

**Usage:**
```tsx
import { LaunchCountdown } from '@/components/launch'

<LaunchCountdown variant="default" />
<LaunchCountdown variant="compact" className="my-4" />
```

**Features:**
- Flip animation on digit changes
- Displays days, hours, minutes, seconds
- Floating particle background
- Auto-hides after launch

---

### LaunchBanner

Prominent banner for hero section with countdown and CTAs.

**Props:**
```typescript
interface LaunchBannerProps {
  onCTAClick?: () => void
  className?: string
}
```

**Usage:**
```tsx
import { LaunchBanner } from '@/components/launch'

<LaunchBanner
  onCTAClick={() => scrollToSection('waitlist')}
  className="mb-12"
/>
```

**Phases:**
- **Pre-launch**: Shows countdown with benefits
- **Launch day**: "WE'RE LIVE!" celebration banner
- **Grace period**: Limited time early adopter benefits
- **Post-launch**: Hides automatically

---

### LaunchModal

First-visit modal with countdown and email capture.

**Props:**
```typescript
interface LaunchModalProps {
  onJoinWaitlist?: () => void
}
```

**Usage:**
```tsx
import { LaunchModal } from '@/components/launch'

<LaunchModal onJoinWaitlist={() => scrollToWaitlist()} />
```

**Features:**
- Appears 2 seconds after first visit
- Email capture for launch reminders
- localStorage persistence (won't show again after dismissal)
- Smooth animations and backdrop blur

---

### LaunchCelebration

Confetti celebration component (no UI, event-driven).

**Usage:**
```tsx
import { LaunchCelebration, triggerLaunchCelebration } from '@/components/launch'

// Automatic (listens for launch-celebration event)
<LaunchCelebration />

// Manual trigger
<button onClick={triggerLaunchCelebration}>Celebrate!</button>
```

**Features:**
- Triggers automatically when countdown reaches zero
- Multi-angle confetti bursts
- Fireworks effect sequence
- 3-second celebration duration
- Session storage prevents duplicate celebrations

---

### CompactCountdown

Inline countdown for text integration.

**Usage:**
```tsx
import { CompactCountdown } from '@/components/launch'

<p>Launching in <CompactCountdown className="font-bold" /></p>
// Output: "Launching in 32d 14h 23m 45s"
```

---

## Configuration

### Launch Config (`launchConfig.ts`)

Central configuration for all launch-related settings.

```typescript
export const LAUNCH_CONFIG = {
  // Launch date in UTC
  launchDate: new Date('2025-12-22T00:00:00Z'),

  // Feature flags
  features: {
    showModal: true,           // First-visit modal
    showBanner: true,          // Hero banner
    showConfetti: true,        // Launch celebration
    enableReminders: true,     // Email reminders
    showCountdownInCTA: true,  // CTA section countdown
  },

  // Messaging for different phases
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
}
```

### Progressive Urgency Levels

Automatically adjusts based on time remaining:

| Level | Days Remaining | Speed Multiplier | Pulse Intensity | Description |
|-------|----------------|------------------|-----------------|-------------|
| 0 | 14+ days | 1.0x | Subtle | Calm, informative |
| 1 | 7-14 days | 1.2x | Noticeable | Building anticipation |
| 2 | 3-7 days | 1.5x | Strong | High urgency |
| 3 | <3 days | 2.0x | Intense | Critical countdown |

**Utility Functions:**
```typescript
getUrgencyLevel()      // Returns 0, 1, 2, or 3
getAnimationSpeed()    // Returns speed multiplier
getPulseIntensity()    // Returns { min, max } scale
getColorIntensity()    // Returns opacity value
```

---

## Usage Examples

### Basic Integration

```tsx
// app/page.tsx
import { LaunchBanner, LaunchModal, LaunchCelebration } from '@/components/launch'

export default function Home() {
  return (
    <main>
      <LaunchBanner onCTAClick={() => scrollToWaitlist()} />
      {/* Other sections */}
      <LaunchModal onJoinWaitlist={() => scrollToWaitlist()} />
      <LaunchCelebration />
    </main>
  )
}
```

### Custom Hook Usage

```tsx
import { useLaunchCountdown } from '@/components/launch'

function MyComponent() {
  const {
    timeRemaining,
    launchPhase,
    formattedLaunchDate,
    isCountdownActive,
    urgencyLevel,
  } = useLaunchCountdown()

  if (!isCountdownActive) {
    return <div>Launch completed!</div>
  }

  return (
    <div>
      <h2>Time until launch:</h2>
      <p>{timeRemaining.days}d {timeRemaining.hours}h</p>
      <p>Urgency level: {urgencyLevel}</p>
      <p>Launch: {formattedLaunchDate}</p>
    </div>
  )
}
```

### Conditional Rendering Based on Phase

```tsx
import { useLaunchCountdown } from '@/components/launch'

function PhaseBasedContent() {
  const { launchPhase } = useLaunchCountdown()

  switch (launchPhase) {
    case 'pre-launch':
      return <PreLaunchContent />
    case 'launch-day':
      return <LaunchDayContent />
    case 'grace-period':
      return <GracePeriodContent />
    case 'post-launch':
      return <PostLaunchContent />
  }
}
```

### Using Progressive Urgency

```tsx
import { useLaunchCountdown, getAnimationSpeed, getPulseIntensity } from '@/components/launch'
import { motion } from 'framer-motion'

function UrgentCTA() {
  const { urgencyLevel } = useLaunchCountdown()
  const speed = getAnimationSpeed(urgencyLevel)
  const pulse = getPulseIntensity(urgencyLevel)

  return (
    <motion.button
      animate={{ scale: [pulse.min, pulse.max, pulse.min] }}
      transition={{
        duration: 1 / speed,  // Faster at higher urgency
        repeat: Infinity,
      }}
    >
      {urgencyLevel === 3 ? 'LAST CHANCE!' : 'Reserve Your Spot'}
    </motion.button>
  )
}
```

---

## API Endpoints

### POST /api/launch-reminder

Email reminder signup endpoint.

**Request Body:**
```typescript
{
  email: string  // Required, validated email
}
```

**Response:**
```typescript
{
  success: boolean
  message: string
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
```

**Integration Points:**
- LaunchModal email capture form
- Can be used in other components
- Ready for backend database integration

---

## Customization

### Change Launch Date

```typescript
// components/launch/launchConfig.ts
launchDate: new Date('2026-01-15T00:00:00Z'),  // January 15, 2026
```

### Disable Features

```typescript
// components/launch/launchConfig.ts
features: {
  showModal: false,           // Hide modal
  showBanner: true,          // Keep banner
  showConfetti: false,        // No celebration
  enableReminders: false,     // No email capture
  showCountdownInCTA: false,  // Hide CTA countdown
}
```

### Adjust Modal Timing

```typescript
// components/launch/useLaunchCountdown.ts
setTimeout(() => {
  setShowModal(true)
}, 5000)  // 5 seconds instead of 2
```

### Customize Urgency Thresholds

```typescript
// components/launch/launchConfig.ts
export function getUrgencyLevel(targetDate: Date): 0 | 1 | 2 | 3 {
  const remaining = getTimeRemaining(targetDate)
  const daysRemaining = remaining.days

  if (daysRemaining < 1) return 3    // Last 24 hours
  if (daysRemaining < 5) return 2    // Last 5 days
  if (daysRemaining < 10) return 1   // Last 10 days
  return 0
}
```

### Customize Confetti Colors

```typescript
// components/launch/LaunchCelebration.tsx
confetti({
  particleCount: 100,
  colors: ['#FF0000', '#00FF00', '#0000FF'],  // Custom colors
})
```

### Update Messaging

```typescript
// components/launch/launchConfig.ts
messages: {
  preLaunch: {
    hero: '⏰ COUNTDOWN TO LAUNCH:',
    modal: 'Get Ready for Something Amazing',
    cta: 'Join the Launch List',
  },
}
```

---

## Testing

### Local Development

```bash
# Start development server
npm run dev

# Visit http://localhost:3000
```

### Test Modal

```typescript
// Clear localStorage to see modal again
localStorage.removeItem('launch-modal-dismissed')

// Reload page and wait 2 seconds
```

### Test Confetti

```typescript
// Open browser console
triggerLaunchCelebration()
```

### Test Different Urgency Levels

```typescript
// Temporarily change launch date in launchConfig.ts
launchDate: new Date('2025-11-25T00:00:00Z'),  // 5 days away

// Rebuild and observe faster animations
npm run build
```

### Test Email Reminder API

```bash
# Using curl
curl -X POST http://localhost:3000/api/launch-reminder \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Check server logs for submission
```

### Test Different Phases

Temporarily adjust dates to test different phases:

```typescript
// Pre-launch (future date)
launchDate: new Date('2025-12-22T00:00:00Z')

// Launch day (today)
launchDate: new Date()

// Grace period (7 days ago)
launchDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

// Post-launch (30 days ago)
launchDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
```

---

## Troubleshooting

### Modal Not Showing

1. Check localStorage: `localStorage.getItem('launch-modal-dismissed')`
2. Clear if needed: `localStorage.removeItem('launch-modal-dismissed')`
3. Verify `features.showModal` is `true` in config
4. Check if in pre-launch phase

### Countdown Not Updating

1. Check browser console for errors
2. Verify launch date is in the future
3. Check if component is mounted
4. Verify `isCountdownActive` is true

### Confetti Not Triggering

1. Verify `features.showConfetti` is `true`
2. Check if `LaunchCelebration` component is mounted
3. Test manually: `triggerLaunchCelebration()`
4. Check browser console for canvas-confetti errors

### Timezone Issues

The system uses UTC for the launch date and automatically converts to the user's local timezone for display. Verify:

1. Launch date is set in UTC: `new Date('2025-12-22T00:00:00Z')`
2. User's browser timezone is correct
3. `formattedLaunchDate` shows correct timezone

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next
npm run build

# Check for missing dependencies
npm install
```

---

## Future Enhancements

### Phase 3 Possibilities

1. **Analytics Integration**
   - Track modal views/dismissals
   - Monitor email capture conversion
   - Countdown engagement metrics
   - A/B testing framework

2. **Email Service Integration**
   - Connect to SendGrid/Mailchimp
   - Automated launch day emails
   - Countdown reminder sequences
   - Email templates

3. **Social Sharing**
   - "Share the countdown" buttons
   - Generate shareable countdown graphics
   - Social meta tags for countdown
   - Twitter/LinkedIn integrations

4. **Advanced Animations**
   - Sound effects (tick, ding, crescendo)
   - More celebration effects
   - Particle systems
   - WebGL backgrounds

5. **Personalization**
   - User-specific countdown messages
   - Personalized email reminders
   - Industry-specific messaging
   - Dynamic benefit highlights

6. **Multi-Launch Support**
   - Support multiple concurrent launches
   - Feature-specific countdowns
   - Regional launch variations
   - Staggered rollout system

---

## Performance Considerations

- **Countdown updates**: Optimized with `setInterval` cleanup
- **Animations**: GPU-accelerated (`transform`, `opacity` only)
- **Modal**: Lazy-loaded, dismissible
- **Confetti**: 3-second limit, automatic cleanup
- **Bundle size**: Tree-shaking enabled, minimal dependencies

---

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design
- IE11: ❌ Not supported (uses modern features)

---

## License

This launch countdown system is part of the Deviant/Deviant website codebase.

---

## Support

For questions or issues:
1. Check this README
2. Review the code comments
3. Test in isolation
4. Contact the development team

**Last Updated:** November 2025
**Version:** 2.0 (Phase 2 Complete)
