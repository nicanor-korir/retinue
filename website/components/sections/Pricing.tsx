"use client"

import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Check, Star } from "lucide-react"

const tiers = [
  {
    name: "Starter",
    description: "Perfect for solo founders and small teams",
    price: "$99",
    earlyBirdPrice: "$49",
    features: [
      "1 department (up to 7 agents)",
      "3 concurrent projects",
      "100 agent-hours/month",
      "Community support",
      "All core features",
    ],
    cta: "Join Waitlist",
    popular: false,
  },
  {
    name: "Professional",
    description: "For growing companies and agencies",
    price: "$499",
    earlyBirdPrice: "$249",
    features: [
      "3 departments (up to 25 agents)",
      "10 concurrent projects",
      "500 agent-hours/month",
      "Priority support",
      "Advanced analytics",
      "API access",
    ],
    cta: "Join Waitlist",
    popular: true,
  },
  {
    name: "Enterprise",
    description: "For large organizations",
    price: "Custom",
    earlyBirdPrice: null,
    features: [
      "Unlimited departments",
      "Unlimited projects",
      "Unlimited agent-hours",
      "Dedicated success manager",
      "Custom agent training",
      "On-premise deployment option",
      "SLA guarantees",
    ],
    cta: "Contact Sales",
    popular: false,
  },
]

const benefits = [
  "50% off for first 6 months",
  "Lifetime priority support",
  "Influence product roadmap",
  "Beta access to new departments",
  "Custom department creation workshop",
]

export function Pricing() {
  return (
    <section id="pricing" className="py-24 bg-white">
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
            Flexible Pricing for Every Stage
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto text-center">
            Join the waitlist now and lock in early adopter pricing - up to 50%
            off
          </p>
        </motion.div>

        {/* Pricing tiers */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2, duration: 0.6 }}
              className="relative"
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
                  <span className="inline-flex items-center gap-1 px-4 py-1 rounded-full bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-white text-sm font-semibold shadow-lg">
                    <Star className="w-4 h-4" />
                    Most Popular
                  </span>
                </div>
              )}

              <Card className={`${tier.popular ? "border-[var(--primary)] border-2 shadow-xl" : ""} flex flex-col h-full`}>
                <CardHeader>
                  <CardTitle className="text-2xl">{tier.name}</CardTitle>
                  <p className="text-[var(--body)]">{tier.description}</p>
                </CardHeader>
                <CardContent className="space-y-6 flex-1 flex flex-col">
                  <div>
                    {tier.earlyBirdPrice ? (
                      <>
                        <div className="flex items-baseline gap-2">
                          <span className="text-4xl font-bold text-[var(--heading)]">
                            {tier.earlyBirdPrice}
                          </span>
                          <span className="text-[var(--body)]">/month</span>
                        </div>
                        <div className="mt-1">
                          <span className="text-[var(--muted)] line-through">
                            {tier.price}/month
                          </span>
                          <span className="ml-2 text-sm text-[var(--primary)] font-semibold">
                            Early bird: 50% off
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="text-4xl font-bold text-[var(--heading)]">
                        {tier.price}
                      </div>
                    )}
                  </div>

                  <ul className="space-y-3 flex-1">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-[var(--primary)] flex-shrink-0 mt-0.5" />
                        <span className="text-[var(--body)]">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    className="w-full mt-auto"
                    variant={tier.popular ? "primary" : "outline"}
                    size="lg"
                  >
                    {tier.cta}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Early adopter benefits */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="max-w-5xl mx-auto"
        >
          <div className="relative">
            {/* Decorative background */}
            <div className="absolute inset-0 bg-gradient-to-r from-[var(--primary)]/5 via-[var(--secondary)]/5 to-[var(--accent)]/5 rounded-3xl blur-xl" />

            <Card className="relative bg-gradient-to-br from-white to-gray-50 border-2 border-[var(--primary)]/30 shadow-2xl">
              <CardContent className="p-10">
                <div className="text-center mb-8">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[var(--secondary)] to-[var(--primary)] text-white rounded-full mb-4 font-semibold">
                    <Star className="w-5 h-5" />
                    <span>Limited Time Offer</span>
                  </div>
                  <h3 className="text-3xl sm:text-4xl font-bold mb-3 bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] bg-clip-text text-transparent">
                    Early Adopter Benefits
                  </h3>
                  <p className="text-lg text-[var(--body)]">
                    Be among the first and get exclusive perks
                  </p>
                </div>

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                  {[
                    {
                      icon: "💰",
                      title: "50% off for first 6 months",
                      description: "Substantial savings on any plan",
                    },
                    {
                      icon: "⏰",
                      title: "Lifetime priority support",
                      description: "Always first in queue",
                    },
                    {
                      icon: "🎯",
                      title: "Influence product roadmap",
                      description: "Your voice shapes our future",
                    },
                    {
                      icon: "🚀",
                      title: "Beta access to new departments",
                      description: "Try new features before anyone else",
                    },
                    {
                      icon: "🛠️",
                      title: "Custom department creation workshop",
                      description: "Build specialized agents with us",
                    },
                    {
                      icon: "👔",
                      title: "Direct founder access",
                      description: "Personal guidance when you need it",
                    },
                  ].map((benefit) => (
                    <div
                      key={benefit.title}
                      className="bg-white rounded-xl p-6 border border-gray-200 hover:border-[var(--primary)] hover:shadow-lg transition-all group"
                    >
                      <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">
                        {benefit.icon}
                      </div>
                      <h4 className="font-bold text-[var(--heading)] mb-2">
                        {benefit.title}
                      </h4>
                      <p className="text-sm text-[var(--body)]">
                        {benefit.description}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="text-center">
                  <p className="text-[var(--body)] mb-4">
                    <strong className="text-[var(--heading)]">Limited to first 100 signups.</strong> Join the waitlist now to secure your spot.
                  </p>
                  <div className="inline-flex items-center gap-2 text-sm text-[var(--muted)]">
                    <Check className="w-4 h-4 text-green-500" />
                    <span>No credit card required</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
