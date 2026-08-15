"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

const faqs = [
  {
    question: "How is Retinue different from ChatGPT or other AI tools?",
    answer:
      "ChatGPT is a single AI assistant. Retinue is a complete company of specialized AI agents that work together with hierarchy, collaboration, and role-specific expertise. Think of it as the difference between hiring a consultant versus hiring an entire department.",
  },
  {
    question: "What kind of work can Retinue actually do?",
    answer:
      "Retinue can handle any knowledge work: software development (backend, frontend, infrastructure), marketing (strategy, content, SEO), sales (outreach, qualification, proposals), operations, finance, research, and more. If a human team can do it, Retinue can too.",
  },
  {
    question: "How much control do I have?",
    answer:
      "Complete control. You approve all strategic decisions, set project parameters, and can intervene at any time. Agents handle execution but you remain the CEO.",
  },
  {
    question: "Is the code/content actually production-ready?",
    answer:
      "Yes. Our agents follow best practices, include testing, documentation, and quality checks. However, we always recommend human review for critical deployments, just like you would with any team.",
  },
  {
    question: "What happens if agents make mistakes?",
    answer:
      "Agents have built-in error handling and escalation. If they encounter blockers or uncertainties, they flag issues for human review. We also maintain complete audit trails so you can see exactly what happened.",
  },
  {
    question: "Can I customize the agents?",
    answer:
      "In Phase 2 and beyond, yes! You'll be able to customize agent behaviors, train them on your specific processes, and even create entirely custom agent roles.",
  },
  {
    question: "What about data security?",
    answer:
      "Your data is encrypted at rest and in transit, isolated per customer, and never used to train our models. We're building toward SOC 2 compliance and offer on-premise deployment for enterprises.",
  },
  {
    question: "How quickly can I get started?",
    answer:
      "Join the waitlist now to get early access. Beta users can typically deploy their first department and start their first project within 30 minutes of onboarding.",
  },
  {
    question: "What's the pricing?",
    answer:
      "We're finalizing pricing tiers. Waitlist members get up to 50% off for the first 6 months as early adopters.",
  },
  {
    question: "Can Retinue replace my entire team?",
    answer:
      "Retinue is designed to augment and accelerate your team, not replace it. Think of it as 10x leverage - you make strategic decisions, agents handle execution. Many solo founders use it to achieve team-level output.",
  },
]

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  return (
    <section id="faq" className="py-24 bg-gray-50">
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
            Frequently Asked Questions
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto">
            Everything you need to know about Retinue
          </p>
        </motion.div>

        {/* FAQ items */}
        <div className="max-w-4xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
            >
              <Card>
                <CardContent className="p-0">
                  <button
                    onClick={() =>
                      setOpenIndex(openIndex === index ? null : index)
                    }
                    className="w-full text-left p-6 flex items-center justify-between gap-4 hover:bg-gray-50 transition-colors"
                  >
                    <h3 className="text-lg font-semibold text-[var(--heading)]">
                      {faq.question}
                    </h3>
                    <ChevronDown
                      className={`w-5 h-5 text-[var(--primary)] flex-shrink-0 transition-transform duration-200 ${
                        openIndex === index ? "transform rotate-180" : ""
                      }`}
                    />
                  </button>

                  <AnimatePresence>
                    {openIndex === index && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6">
                          <p className="text-[var(--body)] leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
