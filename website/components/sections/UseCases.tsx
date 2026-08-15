"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Quote } from "lucide-react"

const cases = [
  {
    industry: "Marketing",
    title: "Campaign Landing Pages",
    challenge:
      "A marketing agency needed 15 client landing pages for a product launch campaign - fast.",
    traditional: { time: "3 weeks", cost: "$12,000" },
    retinue: { time: "8 hours", cost: "$800" },
    results: [
      "All 15 pages deployed same day",
      "Mobile-responsive, brand-matched designs",
      "Integrated with analytics and CRM",
      "93% cost reduction",
    ],
    quote:
      "Retinue is our secret weapon for same-day delivery. What used to take weeks now happens in hours.",
    author: "Marketing Director, Digital Agency",
  },
  {
    industry: "Finance",
    title: "Expense Management System",
    challenge:
      "Finance team drowning in spreadsheets needed custom expense tracking with approval workflows.",
    traditional: { time: "2 months", cost: "$50,000" },
    retinue: { time: "12 hours", cost: "$1,200" },
    results: [
      "Custom approval workflows automated",
      "Real-time reporting dashboard",
      "Integration with accounting software",
      "98% cost reduction, 400x faster",
    ],
    quote:
      "I described our workflow on Monday. By Tuesday we were using the system. Unbelievable.",
    author: "CFO, Mid-Size Company",
  },
  {
    industry: "Manufacturing",
    title: "Inventory Management System",
    challenge:
      "Manufacturing company needed real-time inventory tracking across 3 warehouses with barcode scanning.",
    traditional: { time: "6 months", cost: "$80,000" },
    retinue: { time: "18 hours", cost: "$1,800" },
    results: [
      "Real-time inventory across all locations",
      "Barcode scanning integration",
      "Automated reorder alerts",
      "98% cost reduction, 1000x faster",
    ],
    quote:
      "We've been quoting this project for a year. Retinue built it in a day. Game-changing.",
    author: "Operations Manager, Manufacturing",
  },
  {
    industry: "E-Commerce",
    title: "Multi-Channel Inventory Sync",
    challenge:
      "E-commerce seller needed to sync inventory across Shopify, Amazon, eBay in real-time to prevent overselling.",
    traditional: { time: "Off-the-shelf", cost: "$25,000 setup + ongoing fees" },
    retinue: { time: "9 hours", cost: "$900 one-time" },
    results: [
      "Real-time sync across all platforms",
      "Zero oversells since deployment",
      "Custom business rules implemented",
      "96% cost reduction",
    ],
    quote:
      "The off-the-shelf solutions were expensive and inflexible. Retinue built exactly what we needed.",
    author: "Founder, E-Commerce Brand",
  },
  {
    industry: "Education",
    title: "Course Management Platform",
    challenge:
      "Education startup needed a custom LMS with video hosting, quizzes, certificates, and student dashboards.",
    traditional: { time: "3 months", cost: "$60,000" },
    retinue: { time: "14 hours", cost: "$1,400" },
    results: [
      "Full LMS with video hosting",
      "Automated certificates and tracking",
      "Student and instructor dashboards",
      "98% cost reduction, 650x faster",
    ],
    quote:
      "We were about to pay $60K for an agency. Retinue delivered better results in 14 hours for $1,400.",
    author: "Founder, EdTech Startup",
  },
  {
    industry: "Healthcare",
    title: "Appointment Scheduling System",
    challenge:
      "Medical practice needed HIPAA-compliant scheduling with SMS reminders and patient portal integration.",
    traditional: { time: "Commercial solution", cost: "$15,000 + $500/month" },
    retinue: { time: "11 hours", cost: "$1,100 one-time" },
    results: [
      "HIPAA-compliant booking system",
      "Automated SMS reminders",
      "Integration with existing EMR",
      "93% cost reduction in first year",
    ],
    quote:
      "The commercial solutions were expensive and didn't fit our workflow. Retinue built exactly what we needed.",
    author: "Practice Manager, Medical Clinic",
  },
]

export function UseCases() {
  return (
    <section id="use-cases" className="py-24 bg-gray-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold mb-4">
            Real Results from Real Businesses
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto text-center">
            See how Retinue is building custom software in hours, not months
          </p>
        </motion.div>

        {/* Case study cards */}
        <div className="space-y-8 max-w-5xl mx-auto">
          {cases.map((caseStudy, index) => (
            <motion.div
              key={caseStudy.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2, duration: 0.6 }}
            >
              <Card>
                <CardContent className="p-8 md:p-10">
                  {/* Industry badge */}
                  <div className="inline-block px-3 py-1 bg-[var(--primary)]/10 text-[var(--primary)] rounded-full text-sm font-semibold mb-4">
                    {caseStudy.industry}
                  </div>

                  <h3 className="text-2xl font-bold mb-4 text-[var(--heading)]">
                    {caseStudy.title}
                  </h3>

                  <p className="text-[var(--body)] mb-6">
                    {caseStudy.challenge}
                  </p>

                  {/* Traditional vs Retinue comparison */}
                  <div className="grid md:grid-cols-2 gap-6 mb-8">
                    <div className="border-2 border-gray-200 rounded-lg p-6 bg-white">
                      <h4 className="font-semibold text-gray-500 mb-4 text-sm uppercase tracking-wider">
                        Traditional Approach
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-[var(--body)]">Time:</span>
                          <span className="font-bold text-gray-600">
                            {caseStudy.traditional.time}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[var(--body)]">Cost:</span>
                          <span className="font-bold text-gray-600">
                            {caseStudy.traditional.cost}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="border-2 border-[var(--secondary)] rounded-lg p-6 bg-gradient-to-br from-[var(--secondary)]/5 to-[var(--secondary)]/10 relative overflow-hidden">
                      <div className="absolute top-2 right-2 px-2 py-1 bg-[var(--secondary)] text-white text-xs font-bold rounded">
                        WITH RETINUE
                      </div>
                      <h4 className="font-semibold text-[var(--secondary)] mb-4 text-sm uppercase tracking-wider">
                        Retinue Solution
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-[var(--body)]">Time:</span>
                          <span className="font-bold text-[var(--secondary)] text-lg">
                            {caseStudy.retinue.time}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[var(--body)]">Cost:</span>
                          <span className="font-bold text-[var(--secondary)] text-lg">
                            {caseStudy.retinue.cost}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Results */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-[var(--heading)] mb-3">
                      Results
                    </h4>
                    <ul className="grid md:grid-cols-2 gap-2">
                      {caseStudy.results.map((result, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-[var(--secondary)] mt-1 text-lg">
                            ✓
                          </span>
                          <span className="text-[var(--body)]">{result}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Quote */}
                  <div className="relative border-l-4 border-[var(--primary)] bg-white p-6 rounded-r-lg">
                    <Quote className="w-10 h-10 text-[var(--primary)] opacity-20 mb-3" />
                    <p className="text-lg italic text-[var(--body)] mb-3">
                      "{caseStudy.quote}"
                    </p>
                    <p className="font-semibold text-[var(--heading)]">
                      - {caseStudy.author}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
