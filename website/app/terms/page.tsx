"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { ArrowRight } from "lucide-react"
import { useState } from "react"

export default function TermsOfService() {
  const [activeSection, setActiveSection] = useState("")

  const sections = [
    { id: "agreement", title: "Agreement to Terms" },
    { id: "service", title: "Description of Service" },
    { id: "account", title: "Account Creation" },
    { id: "acceptable-use", title: "Acceptable Use Policy" },
    { id: "intellectual-property", title: "Intellectual Property" },
    { id: "payment", title: "Payment Terms" },
    { id: "availability", title: "Service Availability" },
    { id: "warranties", title: "Warranties and Disclaimers" },
    { id: "liability", title: "Limitation of Liability" },
    { id: "indemnification", title: "Indemnification" },
    { id: "disputes", title: "Dispute Resolution" },
    { id: "termination", title: "Termination" },
    { id: "general", title: "General Provisions" },
  ]

  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-[var(--primary)]/10 via-white to-[var(--accent)]/10 py-20 pt-32">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-4xl mx-auto text-center"
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              Terms of Service
            </h1>
            <p className="text-xl text-[var(--body)] mb-8">
              Last Updated: November 16, 2025
            </p>
            <p className="text-lg text-[var(--body)] max-w-3xl mx-auto">
              Please read these Terms of Service carefully before using Deviant. By accessing or using our services, you agree to be bound by these Terms.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 max-w-5xl">
        <div className="grid lg:grid-cols-4 gap-12">
          {/* Table of Contents - Sticky Sidebar */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-24">
              <h3 className="text-lg font-bold mb-4 text-[var(--heading)]">Table of Contents</h3>
              <nav className="space-y-2">
                {sections.map((section) => (
                  <a
                    key={section.id}
                    href={`#${section.id}`}
                    className={`block text-sm py-2 px-3 rounded-lg transition-colors ${
                      activeSection === section.id
                        ? "bg-[var(--primary)]/10 text-[var(--primary)] font-semibold"
                        : "text-[var(--body)] hover:text-[var(--primary)] hover:bg-gray-50"
                    }`}
                  >
                    {section.title}
                  </a>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 prose prose-lg max-w-none">
            {/* Summary */}
            <Card className="mb-12 bg-gradient-to-br from-[var(--primary)]/5 to-[var(--accent)]/5 border-[var(--primary)]/20">
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                  <ArrowRight className="w-6 h-6 text-[var(--primary)]" />
                  The Short Version
                </h2>
                <ul className="space-y-2 text-[var(--body)]">
                  <li>✅ Use Deviant responsibly</li>
                  <li>✅ You own the code generated</li>
                  <li>✅ We provide the service "as-is"</li>
                  <li>✅ Don't abuse the platform</li>
                  <li>✅ We can terminate for violations</li>
                </ul>
                <p className="mt-4 text-sm text-[var(--muted)] italic">
                  This is a summary. Please read the full terms below for legally binding details.
                </p>
              </CardContent>
            </Card>

            {/* Section 1: Agreement to Terms */}
            <section id="agreement" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">1. Agreement to Terms</h2>

              <h3 className="text-xl font-semibold mb-3">1.1 Binding Agreement</h3>
              <p className="mb-4 text-[var(--body)]">
                By accessing or using Deviant (deviant.eu), you agree to be bound by these Terms. If you don't agree, don't use our services.
              </p>

              <h3 className="text-xl font-semibold mb-3">1.2 Age Requirement</h3>
              <p className="mb-4 text-[var(--body)]">You must be:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>At least 18 years old, OR</li>
                <li>At least 13 years old with parental consent, OR</li>
                <li>At least 16 years old if in the EU</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">1.3 Authority</h3>
              <p className="mb-4 text-[var(--body)]">
                If using Deviant for a company, you have authority to bind that company to these Terms.
              </p>

              <h3 className="text-xl font-semibold mb-3">1.4 Changes to Terms</h3>
              <p className="mb-4 text-[var(--body)]">
                We may update these Terms. We'll notify you of material changes via email, in-app notification, or website banner. Continued use after changes = acceptance.
              </p>
            </section>

            {/* Section 2: Description of Service */}
            <section id="service" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">2. Description of Service</h2>

              <h3 className="text-xl font-semibold mb-3">2.1 What Deviant Provides</h3>
              <p className="mb-4 text-[var(--body)]">
                Deviant is an autonomous AI software development platform featuring:
              </p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>7 specialized AI agents (CEO, CTO, PM, HR, Backend Engineer, Frontend Engineer, Designer)</li>
                <li>Autonomous project execution</li>
                <li>Code generation (Python/FastAPI, React/Next.js)</li>
                <li>Design specifications</li>
                <li>Complete transparency into AI decisions</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">2.2 How It Works</h3>
              <ol className="list-decimal pl-6 mb-4 text-[var(--body)]">
                <li>You provide project descriptions</li>
                <li>AI agents autonomously organize, plan, design, and code</li>
                <li>Generated code and specifications delivered to you</li>
                <li>You review, modify, and deploy as needed</li>
              </ol>

              <h3 className="text-xl font-semibold mb-3">2.3 What Deviant Doesn't Provide</h3>
              <p className="mb-2 text-[var(--body)]">We do NOT provide:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>Code execution environments (you deploy code)</li>
                <li>Hosting services (use your own or third-party)</li>
                <li>Guaranteed uptime (see Section 7)</li>
                <li>Legal advice on code licensing</li>
                <li>Professional liability for deployed code</li>
                <li>Unlimited usage (see plan limits)</li>
              </ul>
            </section>

            {/* Section 3: Account Creation */}
            <section id="account" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">3. Account Creation</h2>

              <h3 className="text-xl font-semibold mb-3">3.1 Account Registration</h3>
              <p className="mb-4 text-[var(--body)]">To use Deviant, you must:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>Provide accurate information</li>
                <li>Maintain account security</li>
                <li>Keep information up-to-date</li>
                <li>Not share account credentials</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">3.2 Account Responsibilities</h3>
              <p className="mb-4 text-[var(--body)]">You are responsible for:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>All activity under your account</li>
                <li>Maintaining security</li>
                <li>Notifying us of unauthorized access</li>
                <li>Complying with these Terms</li>
              </ul>
            </section>

            {/* Section 4: Acceptable Use */}
            <section id="acceptable-use" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">4. Acceptable Use Policy</h2>

              <h3 className="text-xl font-semibold mb-3">4.1 Permitted Uses</h3>
              <p className="mb-4 text-[var(--body)]">You may use Deviant to:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>Build legitimate software applications</li>
                <li>Create business tools and websites</li>
                <li>Develop MVPs and prototypes</li>
                <li>Generate code for commercial use</li>
                <li>Learn and experiment</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">4.2 Prohibited Uses</h3>
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
                <p className="font-semibold text-red-900 mb-3">You may NOT use Deviant to:</p>
                <ul className="space-y-2 text-red-800">
                  <li>❌ Build illegal services or applications</li>
                  <li>❌ Violate laws or regulations</li>
                  <li>❌ Create malware, viruses, or exploits</li>
                  <li>❌ Generate harmful or discriminatory content</li>
                  <li>❌ Overload or disrupt our systems</li>
                  <li>❌ Attempt to reverse engineer our AI agents</li>
                  <li>❌ Share account credentials</li>
                  <li>❌ Create multiple accounts to circumvent limits</li>
                </ul>
              </div>

              <h3 className="text-xl font-semibold mb-3">4.3 Enforcement</h3>
              <p className="mb-4 text-[var(--body)]">
                Violations may result in: warning, account suspension, account termination, legal action, or reporting to authorities.
              </p>
            </section>

            {/* Section 5: Intellectual Property */}
            <section id="intellectual-property" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">5. Intellectual Property</h2>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                <h3 className="text-xl font-semibold mb-3 text-green-900">5.1 Your Code (You Own It!)</h3>
                <p className="mb-4 text-green-900 font-semibold">
                  You own the code generated by Deviant's AI agents.
                </p>
                <p className="mb-4 text-green-800">This means:</p>
                <ul className="list-disc pl-6 text-green-800">
                  <li>Full rights to use, modify, distribute, sell generated code</li>
                  <li>Use commercially without additional fees</li>
                  <li>Claim copyright on generated code</li>
                  <li>No attribution to Deviant required</li>
                </ul>
              </div>

              <h3 className="text-xl font-semibold mb-3">5.2 Deviant's Platform</h3>
              <p className="mb-4 text-[var(--body)]">Deviant retains all rights to:</p>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li>The Deviant platform and infrastructure</li>
                <li>AI agent architecture and prompts</li>
                <li>Trademarks, logos, branding</li>
                <li>Documentation and materials</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">5.3 AI-Generated Content Disclaimer</h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-4">
                <p className="text-yellow-900 mb-2">AI-generated code:</p>
                <ul className="list-disc pl-6 text-yellow-800">
                  <li>May inadvertently resemble existing code</li>
                  <li>Should be reviewed before deployment</li>
                  <li>May require modification for your specific needs</li>
                  <li>Doesn't guarantee uniqueness or originality</li>
                </ul>
                <p className="mt-4 font-semibold text-yellow-900">
                  We recommend code review before production use.
                </p>
              </div>
            </section>

            {/* Section 6: Payment Terms */}
            <section id="payment" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">6. Payment Terms</h2>

              <h3 className="text-xl font-semibold mb-3">6.1 Pricing</h3>
              <ul className="list-disc pl-6 mb-4 text-[var(--body)]">
                <li><strong>Free Tier:</strong> $0/month - Limited usage, Community support</li>
                <li><strong>Professional Tier:</strong> $99/month - Enhanced limits, Priority support</li>
                <li><strong>Enterprise Tier:</strong> Custom pricing - Unlimited usage, Dedicated support</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3">6.2 Billing</h3>
              <p className="mb-4 text-[var(--body)]">
                Subscriptions are billed monthly or annually with auto-renewal unless canceled. Payment via credit card, PayPal, or local methods (M-Pesa).
              </p>

              <h3 className="text-xl font-semibold mb-3">6.3 Refunds</h3>
              <p className="mb-4 text-[var(--body)]">
                No refunds for partial months, unused subscription time, or after project completion. Exceptions for service failures or billing errors.
              </p>
            </section>

            {/* Section 7: Service Availability */}
            <section id="availability" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">7. Service Availability</h2>

              <p className="mb-4 text-[var(--body)]">
                We strive for high availability but don't guarantee 100% uptime or error-free operation. Target uptime: 99.5% (excluding scheduled maintenance).
              </p>
              <p className="mb-4 text-[var(--body)]">
                We may perform scheduled maintenance (with notice) or emergency maintenance (without notice).
              </p>
            </section>

            {/* Section 8: Warranties and Disclaimers */}
            <section id="warranties" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">8. Warranties and Disclaimers</h2>

              <div className="bg-gray-100 border border-gray-300 rounded-lg p-6 mb-6">
                <p className="font-bold text-gray-900 mb-4 text-lg">
                  DEVIANT IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND.
                </p>
                <p className="text-gray-800">This means:</p>
                <ul className="list-disc pl-6 mt-2 text-gray-800">
                  <li>No guarantee of error-free operation</li>
                  <li>No guarantee code will meet your needs</li>
                  <li>No guarantee of specific results</li>
                  <li>You are responsible for reviewing and testing generated code</li>
                </ul>
              </div>

              <h3 className="text-xl font-semibold mb-3">8.1 AI-Generated Code Disclaimer</h3>
              <p className="mb-4 text-[var(--body)]">
                AI-generated code may contain errors or bugs, should be tested before production use, and may require modification. You are responsible for reviewing, testing, ensuring license compliance, and security scanning.
              </p>
            </section>

            {/* Section 9: Limitation of Liability */}
            <section id="liability" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">9. Limitation of Liability</h2>

              <div className="bg-gray-100 border border-gray-300 rounded-lg p-6 mb-6">
                <p className="font-bold text-gray-900 mb-4">
                  TO THE MAXIMUM EXTENT PERMITTED BY LAW, DEVIANT'S TOTAL LIABILITY IS LIMITED TO:
                </p>
                <p className="text-xl font-bold text-gray-900">
                  The amount you paid to Deviant in the 12 months preceding the claim, OR $100 USD, whichever is greater.
                </p>
              </div>

              <p className="mb-4 text-[var(--body)]">
                We are not liable for indirect damages, lost profits, data loss, or third-party claims.
              </p>
            </section>

            {/* Section 10: Indemnification */}
            <section id="indemnification" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">10. Indemnification</h2>

              <p className="mb-4 text-[var(--body)]">
                You agree to indemnify and hold harmless Deviant from claims arising from your use of the service, violations of these Terms, code you deploy, or applications you build.
              </p>
            </section>

            {/* Section 11: Dispute Resolution */}
            <section id="disputes" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">11. Dispute Resolution</h2>

              <h3 className="text-xl font-semibold mb-3">11.1 Informal Resolution</h3>
              <p className="mb-4 text-[var(--body)]">
                Before filing a claim, contact us at legal@deviant.eu. We'll work to resolve within 30 days.
              </p>

              <h3 className="text-xl font-semibold mb-3">11.2 Governing Law</h3>
              <p className="mb-4 text-[var(--body)]">
                These Terms are governed by the laws of Kenya. Jurisdiction: Courts of Nairobi, Kenya.
              </p>

              <h3 className="text-xl font-semibold mb-3">11.3 Arbitration</h3>
              <p className="mb-4 text-[var(--body)]">
                For unresolved disputes, arbitration in Nairobi, Kenya under Kenyan Arbitration Act.
              </p>
            </section>

            {/* Section 12: Termination */}
            <section id="termination" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">12. Termination</h2>

              <h3 className="text-xl font-semibold mb-3">12.1 Termination by You</h3>
              <p className="mb-4 text-[var(--body)]">
                You can terminate anytime by canceling subscription or deleting your account. No refunds for unused time.
              </p>

              <h3 className="text-xl font-semibold mb-3">12.2 Termination by Us</h3>
              <p className="mb-4 text-[var(--body)]">
                We may terminate for Terms violations, illegal activity, non-payment, or abuse of service. Notice provided except for serious violations.
              </p>

              <h3 className="text-xl font-semibold mb-3">12.3 Effect of Termination</h3>
              <p className="mb-4 text-[var(--body)]">
                Upon termination, access ends, but you retain ownership of generated code. Outstanding fees remain due.
              </p>
            </section>

            {/* Section 13: General Provisions */}
            <section id="general" className="mb-12">
              <h2 className="text-3xl font-bold mb-6 text-[var(--heading)]">13. General Provisions</h2>

              <ul className="space-y-3 text-[var(--body)]">
                <li><strong>Entire Agreement:</strong> These Terms constitute the entire agreement between you and Deviant.</li>
                <li><strong>Amendments:</strong> We may modify Terms with notice. Continued use = acceptance.</li>
                <li><strong>Severability:</strong> If any provision is invalid, the rest remains in effect.</li>
                <li><strong>No Agency:</strong> These Terms don't create partnership, agency, or employment relationship.</li>
              </ul>
            </section>

            {/* Contact Information */}
            <Card className="bg-gradient-to-br from-[var(--primary)]/5 to-[var(--accent)]/5 border-[var(--primary)]/20">
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold mb-4 text-[var(--heading)]">Contact Information</h2>
                <div className="space-y-2 text-[var(--body)]">
                  <p><strong>Legal Questions:</strong> legal@deviant.eu</p>
                  <p><strong>Support:</strong> support@deviant.eu</p>
                  <p><strong>Abuse Reports:</strong> abuse@deviant.eu</p>
                  <p className="mt-4"><strong>Mailing Address:</strong> Deviant, Nairobi, Kenya</p>
                </div>
              </CardContent>
            </Card>

            <div className="mt-12 text-center text-sm text-[var(--muted)]">
              <p>Last Updated: November 16, 2025 | Version 1.0</p>
              <p className="mt-2">By using Deviant, you accept these Terms.</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
