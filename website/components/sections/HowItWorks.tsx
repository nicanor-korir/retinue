"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle2, FileText, Play } from "lucide-react"

const steps = [
  {
    number: 1,
    title: "Choose Your Department",
    description:
      "Select from pre-built departments (Marketing, Dev, Sales) or customize your own AI team by choosing specific agent roles and specializations.",
    icon: CheckCircle2,
  },
  {
    number: 2,
    title: "Define Your Project",
    description:
      "Simply describe what you want to accomplish. Our agents understand context, requirements, and business goals just like human teams do.",
    icon: FileText,
  },
  {
    number: 3,
    title: "Watch Your AI Company Work",
    description:
      "Agents collaborate autonomously, escalate strategic decisions to you, and deliver complete, production-ready work. Full transparency into every action.",
    icon: Play,
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-gray-50">
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
            Three Steps to Your AI Company
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto text-center">
            Get started in minutes, not months
          </p>
        </motion.div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2, duration: 0.6 }}
              className="relative"
            >
              {/* Connecting line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-[var(--primary)] to-transparent -z-10" />
              )}

              <Card className="h-full text-center">
                <CardContent className="p-8">
                  {/* Step number */}
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] text-white text-2xl font-bold mb-6">
                    {step.number}
                  </div>

                  {/* Icon */}
                  <div className="mb-6">
                    <step.icon className="w-12 h-12 mx-auto text-[var(--primary)]" />
                  </div>

                  <h3 className="text-2xl font-bold mb-4">{step.title}</h3>
                  <p className="text-[var(--body)] leading-relaxed">
                    {step.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Under the hood section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="mt-16 max-w-4xl mx-auto"
        >
          <Card>
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold mb-6 text-center">
                Under the Hood
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                {[
                  "Hierarchical organization (C-level → Department Heads → Specialists)",
                  "Real-time collaboration and communication",
                  "Smart task delegation and dependency management",
                  "Code review, quality checks, and approval workflows",
                  "Human-in-the-loop for strategic decisions",
                  "Complete audit trail of all agent actions",
                ].map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] mt-2 flex-shrink-0" />
                    <span className="text-[var(--body)]">{feature}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  )
}
