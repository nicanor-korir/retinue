"use client"

import { motion } from "framer-motion"
import { DollarSign, Clock, TrendingUp } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

const problems = [
  {
    icon: DollarSign,
    title: "Hiring is Expensive",
    description:
      "A single senior developer costs $120K+/year. A marketing team? $300K+. Most businesses can't afford full departments.",
    color: "var(--primary)",
  },
  {
    icon: Clock,
    title: "Time to Market is Critical",
    description:
      "Waiting weeks to hire, onboard, and ramp up talent means missing opportunities and losing to competitors.",
    color: "var(--accent)",
  },
  {
    icon: TrendingUp,
    title: "Scaling is Hard",
    description:
      "Growing your team linearly doesn't work. You need 10x leverage, not 10% improvements.",
    color: "var(--secondary)",
  },
]

export function ProblemStatement() {
  return (
    <section id="problem" className="py-24 bg-gray-50">
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
            The Challenge Every Business Faces
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto text-center">
            Building and scaling teams the traditional way is slow, expensive, and
            limiting
          </p>
        </motion.div>

        {/* Problem cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {problems.map((problem, index) => (
            <motion.div
              key={problem.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2, duration: 0.6 }}
            >
              <Card className="h-full">
                <CardContent className="p-8">
                  <div
                    className="w-16 h-16 rounded-lg flex items-center justify-center mb-6"
                    style={{
                      backgroundColor: `${problem.color}15`,
                    }}
                  >
                    <problem.icon
                      className="w-8 h-8"
                      style={{ color: problem.color }}
                    />
                  </div>
                  <h3 className="text-2xl font-bold mb-4">{problem.title}</h3>
                  <p className="text-[var(--body)] leading-relaxed">
                    {problem.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
