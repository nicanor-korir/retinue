"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Cookie } from "lucide-react"

export default function CookiePolicy() {
  const cookieTypes = [
    {
      name: "Essential Cookies",
      purpose: "Required for site functionality",
      duration: "Session / 30 days",
      examples: ["Authentication", "Session management", "Security features"],
      canDisable: false,
    },
    {
      name: "Analytics Cookies",
      purpose: "Help us understand usage patterns",
      duration: "Up to 2 years",
      examples: ["Page views", "Feature usage", "Performance monitoring"],
      canDisable: true,
    },
    {
      name: "Preference Cookies",
      purpose: "Remember your settings",
      duration: "Up to 1 year",
      examples: ["Language", "Theme", "UI customization"],
      canDisable: true,
    },
  ]

  return (
    <main className="min-h-screen bg-white">
      <section className="bg-gradient-to-br from-[var(--primary)]/10 via-white to-[var(--accent)]/10 py-20 pt-32">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto text-center"
          >
            <Cookie className="w-16 h-16 mx-auto mb-6 text-[var(--primary)]" />
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              Cookie Policy
            </h1>
            <p className="text-xl text-[var(--body)] mb-8">
              Last Updated: November 16, 2025
            </p>
            <p className="text-lg text-[var(--body)] max-w-3xl mx-auto">
              This Cookie Policy explains how Retinue uses cookies and similar technologies.
            </p>
          </motion.div>
        </div>
      </section>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 max-w-4xl">
        <div className="prose prose-lg max-w-none">
          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">What Are Cookies?</h2>
            <p className="mb-4 text-[var(--body)]">
              Cookies are small text files stored on your device when you visit websites. They help websites remember your preferences, keep you logged in, and understand how you use the site.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">Cookies We Use</h2>
            <div className="space-y-6">
              {cookieTypes.map((cookie, index) => (
                <Card key={cookie.name} className={cookie.canDisable ? "" : "border-2 border-[var(--primary)]/30"}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-xl font-semibold text-[var(--heading)]">{cookie.name}</h3>
                      {!cookie.canDisable && (
                        <span className="px-3 py-1 bg-[var(--primary)]/10 text-[var(--primary)] text-sm font-semibold rounded-full">
                          Required
                        </span>
                      )}
                    </div>
                    <p className="mb-3 text-[var(--body)]">
                      <strong>Purpose:</strong> {cookie.purpose}
                    </p>
                    <p className="mb-3 text-[var(--body)]">
                      <strong>Duration:</strong> {cookie.duration}
                    </p>
                    <div className="mb-3">
                      <strong className="text-[var(--body)]">Examples:</strong>
                      <ul className="list-disc pl-6 mt-2 text-[var(--body)]">
                        {cookie.examples.map((example) => (
                          <li key={example}>{example}</li>
                        ))}
                      </ul>
                    </div>
                    <p className="text-sm text-[var(--muted)]">
                      {cookie.canDisable
                        ? "✓ You can disable these cookies in your browser settings"
                        : "⚠ Disabling these cookies may affect site functionality"}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">Third-Party Cookies</h2>
            <p className="mb-4 text-[var(--body)]">We may use third-party cookies from:</p>
            <ul className="list-disc pl-6 mb-4 text-[var(--body)] space-y-2">
              <li><strong>Google Analytics</strong> (if enabled) - Website analytics and performance</li>
              <li><strong>Stripe</strong> - Payment processing (only on payment pages)</li>
              <li><strong>Support Chat</strong> (if implemented) - Customer support</li>
            </ul>
            <p className="text-[var(--body)]">
              These third parties have their own cookie policies. We don't control their cookies.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">How to Control Cookies</h2>

            <Card className="mb-6 bg-blue-50 border-blue-200">
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-3 text-blue-900">Browser Settings</h3>
                <p className="text-blue-800 mb-3">
                  You can control cookies through your browser settings:
                </p>
                <ul className="list-disc pl-6 text-blue-800 space-y-1">
                  <li><strong>Chrome:</strong> Settings → Privacy and security → Cookies</li>
                  <li><strong>Firefox:</strong> Options → Privacy & Security → Cookies</li>
                  <li><strong>Safari:</strong> Preferences → Privacy → Cookies</li>
                  <li><strong>Edge:</strong> Settings → Privacy → Cookies</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="mb-6">
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-3">Opt-Out Options</h3>
                <ul className="list-disc pl-6 text-[var(--body)] space-y-2">
                  <li><strong>Analytics:</strong> You can opt out via browser settings or cookie preferences</li>
                  <li><strong>Do Not Track:</strong> We honor "Do Not Track" signals from your browser</li>
                  <li><strong>Preferences:</strong> Managed in Account Settings (when logged in)</li>
                </ul>
              </CardContent>
            </Card>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <p className="text-yellow-900 font-semibold mb-2">⚠ Important</p>
              <p className="text-yellow-800">
                Disabling essential cookies may prevent you from using certain features of Retinue, such as logging in or saving preferences.
              </p>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">Data Collected by Cookies</h2>
            <p className="mb-4 text-[var(--body)]">Cookies may collect:</p>
            <ul className="list-disc pl-6 mb-4 text-[var(--body)] space-y-2">
              <li>Pages you visit on Retinue</li>
              <li>Features you use</li>
              <li>Time spent on pages</li>
              <li>Browser and device information</li>
              <li>Login session data</li>
              <li>Preference settings</li>
            </ul>
            <p className="text-[var(--body)]">
              This data is used to improve our service and is subject to our <a href="/privacy" className="text-[var(--primary)] hover:underline">Privacy Policy</a>.
            </p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">Updates to This Policy</h2>
            <p className="mb-4 text-[var(--body)]">
              We may update this Cookie Policy from time to time. We'll notify you of material changes via email or in-app notification.
            </p>
            <p className="text-[var(--body)]">
              Continued use of Retinue after changes constitutes acceptance of the updated policy.
            </p>
          </section>

          <Card className="bg-gradient-to-br from-[var(--primary)]/5 to-[var(--accent)]/5 border-[var(--primary)]/20">
            <CardContent className="p-8">
              <h2 className="text-2xl font-bold mb-4 text-[var(--heading)]">Questions?</h2>
              <p className="mb-2 text-[var(--body)]">
                If you have questions about our use of cookies, contact us:
              </p>
              <p className="text-[var(--body)]">
                <strong>Email:</strong> privacy@retinue.team<br />
                <strong>Address:</strong> Retinue, Nairobi, Kenya
              </p>
            </CardContent>
          </Card>

          <div className="mt-12 text-center text-sm text-[var(--muted)]">
            <p>Last Updated: November 16, 2025 | Version 1.0</p>
            <p className="mt-2">
              See also: <a href="/privacy" className="text-[var(--primary)] hover:underline">Privacy Policy</a> | <a href="/terms" className="text-[var(--primary)] hover:underline">Terms of Service</a>
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
