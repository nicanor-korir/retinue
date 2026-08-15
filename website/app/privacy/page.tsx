"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Shield } from "lucide-react"
import Link from "next/link"

export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-white">
      <section className="bg-gradient-to-br from-[var(--primary)]/10 via-white to-[var(--accent)]/10 py-20 pt-32">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto text-center">
            <Shield className="w-16 h-16 mx-auto mb-6 text-[var(--primary)]" />
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">Privacy Policy</h1>
            <p className="text-xl text-[var(--body)] mb-8">Last Updated: November 16, 2025</p>
            <p className="text-lg text-[var(--body)] max-w-3xl mx-auto">
              At Retinue, we're committed to radical transparency - including how we handle your data.
            </p>
          </motion.div>
        </div>
      </section>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 max-w-4xl">
        <Card className="mb-8 bg-gradient-to-br from-[var(--primary)]/5 to-[var(--accent)]/5">
          <CardContent className="p-8">
            <h2 className="text-2xl font-bold mb-4">Quick Summary</h2>
            <ul className="space-y-2 text-[var(--body)]">
              <li>✅ We collect only what's needed to provide our service</li>
              <li>✅ We never sell your data</li>
              <li>✅ You own all generated code</li>
              <li>✅ AI usage is fully transparent</li>
              <li>✅ You can opt-out of AI training</li>
            </ul>
          </CardContent>
        </Card>

        <div className="prose prose-lg max-w-none">
          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">1. Who We Are</h2>
            <p className="mb-4"><strong>Company:</strong> Retinue<br/><strong>Location:</strong> Nairobi, Kenya<br/><strong>Contact:</strong> privacy@retinue.team<br/><strong>DPO:</strong> dpo@retinue.team</p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">2. Information We Collect</h2>
            <h3 className="text-xl font-semibold mb-3">Account Information</h3>
            <p className="mb-4">Name, email, password (encrypted), company name (optional), billing information</p>
            <h3 className="text-xl font-semibold mb-3">Project Information</h3>
            <p className="mb-4">Project descriptions, requirements, specifications, generated code</p>
            <h3 className="text-xl font-semibold mb-3">Usage Data</h3>
            <p className="mb-4">Pages visited, features used, IP address, browser type, device information</p>
            <h3 className="text-xl font-semibold mb-3">AI-Generated Data</h3>
            <p className="mb-4">Agent communications, decisions, code generation logs - all visible to you in real-time</p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide and improve our services</li>
              <li>Process projects through AI agents</li>
              <li>Customer support and communication</li>
              <li>Security and fraud prevention</li>
              <li>AI training (anonymized, opt-out available)</li>
            </ul>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">4. How We Share Information</h2>
            <h3 className="text-xl font-semibold mb-3">Service Providers</h3>
            <ul className="list-disc pl-6 space-y-2 mb-4">
              <li><strong>Anthropic:</strong> AI processing (Claude API)</li>
              <li><strong>Cloud Hosting:</strong> Infrastructure and data storage</li>
              <li><strong>Stripe:</strong> Payment processing</li>
            </ul>
            <Card className="bg-red-50 border-red-200">
              <CardContent className="p-6">
                <h4 className="font-bold text-red-900 mb-2">We NEVER:</h4>
                <ul className="list-disc pl-6 text-red-800">
                  <li>Sell your data</li>
                  <li>Share for advertising</li>
                  <li>Provide your code to others</li>
                </ul>
              </CardContent>
            </Card>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">5. AI-Specific Practices</h2>
            <p className="mb-4"><strong>Data Flow:</strong> Your Input → Our Servers → Anthropic API → AI Response → You</p>
            <p className="mb-4"><strong>Transparency:</strong> Unlike black-box AI, you see all decisions in real-time</p>
            <p className="mb-4"><strong>Training:</strong> Anonymized data may improve agents (opt-out available)</p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">6. Data Security</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <Card>
                <CardContent className="p-6">
                  <h4 className="font-bold mb-2">Technical</h4>
                  <ul className="text-sm space-y-1">
                    <li>✓ TLS/SSL encryption</li>
                    <li>✓ AES-256 at rest</li>
                    <li>✓ Password hashing</li>
                    <li>✓ Regular audits</li>
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <h4 className="font-bold mb-2">Organizational</h4>
                  <ul className="text-sm space-y-1">
                    <li>✓ Access controls</li>
                    <li>✓ Employee training</li>
                    <li>✓ Incident response</li>
                    <li>✓ Regular backups</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">7. Your Rights</h2>
            <h3 className="text-xl font-semibold mb-3">All Users Can:</h3>
            <ul className="list-disc pl-6 space-y-2 mb-4">
              <li>Access and export your data</li>
              <li>Delete projects or account</li>
              <li>Opt out of marketing</li>
              <li>Opt out of AI training</li>
              <li>Mark projects confidential</li>
            </ul>
            <h3 className="text-xl font-semibold mb-3">GDPR Rights (EU)</h3>
            <p className="mb-4">Access, rectification, erasure, portability, object to processing, withdraw consent, complain to authorities</p>
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="p-6">
                <h4 className="font-bold text-blue-900 mb-2">Exercise Your Rights:</h4>
                <p className="text-blue-800">Email privacy@retinue.team - We respond within 30 days, no charge for reasonable requests</p>
              </CardContent>
            </Card>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">8. Data Retention</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Active accounts:</strong> Retained while active</li>
              <li><strong>Projects:</strong> Retained until you delete</li>
              <li><strong>Closed accounts:</strong> Deleted within 30 days</li>
              <li><strong>Financial records:</strong> 7 years (legal requirement)</li>
            </ul>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">9. International Transfers</h2>
            <p className="mb-4">Your data may be transferred to the US (Anthropic, cloud providers). We use Standard Contractual Clauses for EU data protection.</p>
          </section>

          <section className="mb-12">
            <h2 className="text-3xl font-bold mb-6">10. Cookies</h2>
            <p className="mb-4">We use essential cookies (authentication), analytics cookies (usage patterns), and preference cookies (settings). <Link href="/cookies" className="text-[var(--primary)] hover:underline">See full Cookie Policy</Link>.</p>
          </section>

          <Card className="bg-gradient-to-br from-[var(--primary)]/5 to-[var(--accent)]/5">
            <CardContent className="p-8">
              <h2 className="text-2xl font-bold mb-4">Contact Us</h2>
              <p><strong>Privacy:</strong> privacy@retinue.team</p>
              <p><strong>DPO:</strong> dpo@retinue.team</p>
              <p><strong>Security:</strong> security@retinue.team</p>
              <p className="mt-4"><strong>Address:</strong> Retinue, Nairobi, Kenya</p>
              <p className="mt-4 text-sm text-[var(--muted)]">Response within 72 hours</p>
            </CardContent>
          </Card>

          <div className="mt-12 text-center text-sm text-[var(--muted)]">
            <p>Last Updated: November 16, 2025 | Version 1.0</p>
          </div>
        </div>
      </div>
    </main>
  )
}
