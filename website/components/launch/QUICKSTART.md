# Launch Countdown Quick Start Guide

Get the launch countdown system up and running in minutes.

## 🚀 5-Minute Setup

### 1. Install Dependencies

```bash
cd Domains/02-shoman-saas-domain/apps/Retinue/website
npm install canvas-confetti
npm install --save-dev @types/canvas-confetti
```

### 2. Add to Your Page

```tsx
// app/page.tsx
"use client"

import { LaunchBanner, LaunchModal, LaunchCelebration } from '@/components/launch'

export default function Home() {
  const scrollToWaitlist = () => {
    document.getElementById('waitlist')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <main>
      {/* Add countdown banner to hero */}
      <LaunchBanner onCTAClick={scrollToWaitlist} />

      {/* Your existing content */}
      <YourHeroSection />
      <YourFeatures />
      <YourWaitlistForm id="waitlist" />

      {/* Add modal and celebration */}
      <LaunchModal onJoinWaitlist={scrollToWaitlist} />
      <LaunchCelebration />
    </main>
  )
}
```

### 3. Configure Launch Date

```typescript
// components/launch/launchConfig.ts
export const LAUNCH_CONFIG = {
  launchDate: new Date('2025-12-22T00:00:00Z'),  // Your launch date
  // ... rest of config
}
```

### 4. Test It

```bash
npm run dev
# Visit http://localhost:3000
# Wait 2 seconds for modal
```

**That's it!** You now have a complete launch countdown system.

---

## 📚 Common Use Cases

### Use Case 1: Just the Countdown Banner

Minimal integration - just show countdown in hero section.

```tsx
import { LaunchBanner } from '@/components/launch'

<Hero>
  <LaunchBanner onCTAClick={() => scrollToWaitlist()} />
  <h1>Your Headline</h1>
  <p>Your subheadline</p>
</Hero>
```

---

### Use Case 2: Countdown + Modal (Recommended)

Full experience with first-visit modal.

```tsx
import { LaunchBanner, LaunchModal } from '@/components/launch'

<main>
  <LaunchBanner onCTAClick={scrollToWaitlist} />
  {/* Your content */}
  <LaunchModal onJoinWaitlist={scrollToWaitlist} />
</main>
```

---

### Use Case 3: Inline Countdown Text

Add countdown directly in text content.

```tsx
import { CompactCountdown } from '@/components/launch'

<p>
  We're launching in <CompactCountdown className="font-bold text-primary" />!
  Join the waitlist to be notified.
</p>
// Output: "We're launching in 32d 14h 23m 45s! Join..."
```

---

### Use Case 4: Custom Countdown Display

Build your own countdown UI using the hook.

```tsx
import { useLaunchCountdown } from '@/components/launch'

function CustomCountdown() {
  const { timeRemaining, isCountdownActive } = useLaunchCountdown()

  if (!isCountdownActive) return null

  return (
    <div className="grid grid-cols-4 gap-4">
      <div>
        <div className="text-4xl font-bold">{timeRemaining.days}</div>
        <div className="text-sm">Days</div>
      </div>
      <div>
        <div className="text-4xl font-bold">{timeRemaining.hours}</div>
        <div className="text-sm">Hours</div>
      </div>
      <div>
        <div className="text-4xl font-bold">{timeRemaining.minutes}</div>
        <div className="text-sm">Minutes</div>
      </div>
      <div>
        <div className="text-4xl font-bold">{timeRemaining.seconds}</div>
        <div className="text-sm">Seconds</div>
      </div>
    </div>
  )
}
```

---

### Use Case 5: Phase-Based Content

Show different content based on launch phase.

```tsx
import { useLaunchCountdown } from '@/components/launch'

function PhaseBasedHero() {
  const { launchPhase } = useLaunchCountdown()

  return (
    <div>
      {launchPhase === 'pre-launch' && (
        <>
          <h1>Coming Soon!</h1>
          <p>Reserve your early access spot</p>
        </>
      )}

      {launchPhase === 'launch-day' && (
        <>
          <h1>We're Live!</h1>
          <p>Start building today</p>
        </>
      )}

      {launchPhase === 'grace-period' && (
        <>
          <h1>Early Adopter Benefits!</h1>
          <p>Get 50% off for 6 months - limited time</p>
        </>
      )}

      {launchPhase === 'post-launch' && (
        <>
          <h1>Build Software as Fast as You Can Describe It</h1>
          <p>Join 1000+ companies already building with Retinue</p>
        </>
      )}
    </div>
  )
}
```

---

### Use Case 6: Urgent CTA with Progressive Intensity

CTA that gets more urgent as launch approaches.

```tsx
import { useLaunchCountdown, getAnimationSpeed, getPulseIntensity } from '@/components/launch'
import { motion } from 'framer-motion'

function UrgentCTA() {
  const { urgencyLevel, timeRemaining } = useLaunchCountdown()
  const speed = getAnimationSpeed(urgencyLevel)
  const pulse = getPulseIntensity(urgencyLevel)

  const messages = {
    0: 'Join the Waitlist',
    1: 'Reserve Your Spot',
    2: 'Limited Spots Remaining',
    3: 'LAST CHANCE - Hours Remaining!',
  }

  return (
    <motion.button
      animate={{ scale: [pulse.min, pulse.max, pulse.min] }}
      transition={{
        duration: 1 / speed,
        repeat: Infinity,
      }}
      className={`
        px-8 py-4 rounded-full font-bold
        ${urgencyLevel >= 2 ? 'bg-red-500' : 'bg-primary'}
        ${urgencyLevel === 3 ? 'ring-4 ring-red-300 animate-pulse' : ''}
      `}
    >
      {messages[urgencyLevel]}
    </motion.button>
  )
}
```

---

### Use Case 7: Email Reminder Only (No Full Waitlist)

Lightweight email capture for launch reminders.

```tsx
'use client'

import { useState } from 'react'

function QuickReminder() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    const response = await fetch('/api/launch-reminder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })

    if (response.ok) {
      setSuccess(true)
      setEmail('')
    }

    setLoading(false)
  }

  if (success) {
    return <p className="text-green-600">✓ You'll get a reminder on launch day!</p>
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="your@email.com"
        required
        className="px-4 py-2 border rounded"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-6 py-2 bg-primary text-white rounded"
      >
        {loading ? 'Sending...' : 'Remind Me'}
      </button>
    </form>
  )
}
```

---

### Use Case 8: Conditional Feature Flags

Show/hide components based on configuration.

```tsx
import { LAUNCH_CONFIG } from '@/components/launch'
import { LaunchBanner, LaunchModal } from '@/components/launch'

function ConditionalLaunch() {
  return (
    <div>
      {LAUNCH_CONFIG.features.showBanner && (
        <LaunchBanner onCTAClick={scrollToWaitlist} />
      )}

      {/* Your content */}

      {LAUNCH_CONFIG.features.showModal && (
        <LaunchModal onJoinWaitlist={scrollToWaitlist} />
      )}
    </div>
  )
}
```

---

## 🎨 Styling Tips

### Match Your Brand Colors

```tsx
// Customize in your component
<div className="bg-gradient-to-r from-your-primary via-your-accent to-your-secondary">
  <LaunchCountdown />
</div>
```

### Custom Countdown Styling

```tsx
<LaunchCountdown
  className="
    rounded-3xl
    shadow-2xl
    p-8
    bg-gradient-to-br from-blue-500 to-purple-600
  "
/>
```

---

## 🔧 Quick Tweaks

### Change Modal Delay

```typescript
// components/launch/useLaunchCountdown.ts (line ~106)
setTimeout(() => {
  setShowModal(true)
}, 5000)  // 5 seconds instead of 2
```

### Disable Modal After Testing

```typescript
// components/launch/launchConfig.ts
features: {
  showModal: false,  // Set to false
}
```

### Change Urgency Thresholds

```typescript
// components/launch/launchConfig.ts
export function getUrgencyLevel(targetDate: Date): 0 | 1 | 2 | 3 {
  const remaining = getTimeRemaining(targetDate)
  const daysRemaining = remaining.days

  if (daysRemaining < 2) return 3    // Last 48 hours
  if (daysRemaining < 7) return 2    // Last week
  if (daysRemaining < 14) return 1   // Last 2 weeks
  return 0
}
```

---

## 🧪 Testing Checklist

- [ ] Countdown displays correctly
- [ ] Countdown updates every second
- [ ] Modal appears after 2 seconds on first visit
- [ ] Modal doesn't appear after dismissal
- [ ] Email reminder form submits successfully
- [ ] Confetti triggers (test with `triggerLaunchCelebration()`)
- [ ] Responsive on mobile devices
- [ ] Works in different timezones
- [ ] Urgency level increases as launch approaches
- [ ] Build completes without errors (`npm run build`)

---

## ❓ FAQ

**Q: How do I test the modal again after dismissing it?**

A: Clear localStorage:
```javascript
localStorage.removeItem('launch-modal-dismissed')
```
Then reload the page.

---

**Q: Can I use this for multiple launches?**

A: Currently supports one launch at a time. For multiple launches, duplicate the component structure with different config files.

---

**Q: How do I integrate with my email service?**

A: Modify `/app/api/launch-reminder/route.ts` to connect to your email service:

```typescript
// Example with SendGrid
import sgMail from '@sendgrid/mail'

sgMail.setApiKey(process.env.SENDGRID_API_KEY!)

export async function POST(request: NextRequest) {
  const { email } = await request.json()

  // Save to database
  await db.launch_reminders.create({ email })

  // Send confirmation email
  await sgMail.send({
    to: email,
    from: 'hello@retinue.team',
    subject: 'Launch Day Reminder Confirmed',
    html: '<p>We'll remind you on launch day!</p>',
  })

  return NextResponse.json({ success: true })
}
```

---

**Q: Can I change the launch date after deployment?**

A: Yes, just update `launchDate` in `launchConfig.ts` and redeploy. The countdown will automatically adjust.

---

**Q: How do I add sound effects?**

A: Add audio elements and trigger on urgency level changes:

```tsx
import { useLaunchCountdown } from '@/components/launch'
import { useEffect, useRef } from 'react'

function CountdownWithSound() {
  const { timeRemaining, urgencyLevel } = useLaunchCountdown()
  const tickSound = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    if (urgencyLevel >= 2 && timeRemaining.seconds % 1 === 0) {
      tickSound.current?.play()
    }
  }, [timeRemaining.seconds, urgencyLevel])

  return (
    <>
      <audio ref={tickSound} src="/sounds/tick.mp3" preload="auto" />
      <LaunchCountdown />
    </>
  )
}
```

---

## 📞 Need Help?

1. Check the [main README](./README.md) for detailed documentation
2. Review the component source code (well-commented)
3. Test in isolation to identify issues
4. Contact the development team

---

**Happy Launching! 🚀**
