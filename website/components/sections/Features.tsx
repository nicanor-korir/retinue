"use client"

import { motion } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import {
  Zap,
  DollarSign,
  Target,
  Clock,
  Eye,
  Hand,
  Link2,
  TrendingUp,
  Shield,
} from "lucide-react"

const features = [
  {
    icon: Zap,
    title: "10-100x Faster",
    description:
      "Complete projects in hours that would take teams weeks. Marketing campaigns, software development, research reports - all delivered at unprecedented speed.",
    color: "var(--primary)",
  },
  {
    icon: DollarSign,
    title: "1/100th the Cost",
    description:
      "Pay for AI agents at a fraction of human salaries. A full marketing department for the cost of a single junior marketer.",
    color: "var(--accent)",
  },
  {
    icon: Target,
    title: "Specialized Expertise",
    description:
      "Each agent is trained on best practices, industry standards, and cutting-edge techniques. Get senior-level output from every agent.",
    color: "var(--secondary)",
  },
  {
    icon: Clock,
    title: "24/7 Operation",
    description:
      "Your AI company never sleeps, takes vacations, or burns out. Continuous progress on all projects, day and night.",
    color: "var(--primary)",
  },
  {
    icon: Eye,
    title: "Complete Transparency",
    description:
      "See exactly what every agent is working on, how decisions are made, and track progress in real-time. No black boxes.",
    color: "var(--accent)",
  },
  {
    icon: Hand,
    title: "Human Control",
    description:
      "Strategic decisions always come to you for approval. You stay in control while agents handle execution.",
    color: "var(--secondary)",
  },
  {
    icon: Link2,
    title: "Seamless Integration",
    description:
      "Connects with your existing tools: GitHub, Slack, Google Workspace, CRM systems, and more.",
    color: "var(--primary)",
  },
  {
    icon: TrendingUp,
    title: "Continuously Improving",
    description:
      "Agents learn from feedback, update with new best practices, and improve with every project.",
    color: "var(--accent)",
  },
  {
    icon: Shield,
    title: "Enterprise-Grade Security",
    description:
      "Your data is encrypted, isolated, and secure. SOC 2 compliant with audit trails for every action.",
    color: "var(--secondary)",
  },
]

export function Features() {
  return (
    <section id="features" className="py-24 bg-white">
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
            Why Deviant is Different
          </h2>
          <p className="text-xl text-[var(--body)] max-w-3xl mx-auto text-center">
            Not just another AI tool - a complete paradigm shift in how work gets
            done
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.6 }}
            >
              <Card className="h-full">
                <CardContent className="p-6">
                  <div
                    className="w-14 h-14 rounded-lg flex items-center justify-center mb-4"
                    style={{
                      backgroundColor: `${feature.color}15`,
                    }}
                  >
                    <feature.icon
                      className="w-7 h-7"
                      style={{ color: feature.color }}
                    />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                  <p className="text-[var(--body)] leading-relaxed">
                    {feature.description}
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
