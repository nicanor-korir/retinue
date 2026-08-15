"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import {
  Megaphone,
  Code,
  Users,
  BarChart,
  Headphones,
  Sparkles,
} from "lucide-react"

const departments = [
  {
    id: "marketing",
    name: "Marketing Department",
    icon: Megaphone,
    color: "var(--primary)",
    agents: [
      "CMO",
      "Content Strategist",
      "SEO Specialist",
      "Social Media Manager",
      "Email Marketer",
      "Analytics Expert",
    ],
    tasks: [
      "Develop comprehensive marketing strategies",
      "Create content calendars and campaigns",
      "Write blog posts, social media content, email sequences",
      "Optimize for SEO and conversions",
      "Analyze performance and iterate",
    ],
    useCase:
      "Launch a complete content marketing campaign for a SaaS product in 24 hours",
  },
  {
    id: "development",
    name: "Software Development",
    icon: Code,
    color: "var(--accent)",
    agents: [
      "CTO",
      "Tech Lead",
      "Backend Engineers (3)",
      "Frontend Engineers (2)",
      "QA Engineer",
      "DevOps",
      "Designer",
    ],
    tasks: [
      "Evaluate technical requirements",
      "Design system architecture",
      "Write production-ready code (Python, JavaScript, etc.)",
      "Implement CI/CD pipelines",
      "Create UI/UX designs",
      "Test and deploy applications",
    ],
    useCase:
      "Build and deploy a full-stack SaaS MVP in 3 days instead of 3 months",
  },
  {
    id: "sales",
    name: "Sales & Business Development",
    icon: Users,
    color: "var(--secondary)",
    agents: [
      "VP Sales",
      "Account Executives (2)",
      "SDRs (3)",
      "Sales Ops",
      "Customer Success Manager",
    ],
    tasks: [
      "Develop sales strategies and playbooks",
      "Generate and qualify leads",
      "Create personalized outreach campaigns",
      "Handle objections and close deals",
      "Onboard and support customers",
      "Analyze sales metrics",
    ],
    useCase:
      "Run a complete outbound sales campaign with personalized sequences for 1,000 prospects",
  },
  {
    id: "operations",
    name: "Operations & Finance",
    icon: BarChart,
    color: "var(--primary)",
    agents: [
      "COO",
      "CFO",
      "Financial Analyst",
      "Operations Manager",
      "Data Analyst",
      "Compliance Officer",
    ],
    tasks: [
      "Create financial models and forecasts",
      "Optimize operational processes",
      "Generate reports and dashboards",
      "Ensure regulatory compliance",
      "Analyze business metrics",
      "Recommend strategic decisions",
    ],
    useCase:
      "Build a comprehensive 5-year financial model and operational roadmap in 2 hours",
  },
  {
    id: "support",
    name: "Customer Support",
    icon: Headphones,
    color: "var(--accent)",
    agents: [
      "Support Manager",
      "Support Specialists (3)",
      "Technical Support",
      "QA Specialist",
    ],
    tasks: [
      "Answer customer inquiries 24/7",
      "Troubleshoot technical issues",
      "Create help documentation",
      "Escalate complex issues appropriately",
      "Track satisfaction metrics",
      "Improve support processes",
    ],
    useCase:
      "Handle 1,000+ support tickets per day with 95% satisfaction rate",
  },
  {
    id: "custom",
    name: "Build Your Own",
    icon: Sparkles,
    color: "var(--secondary)",
    agents: ["Fully Customizable", "Mix & Match Roles"],
    tasks: [
      "Legal team (lawyers, paralegals, compliance)",
      "HR department (recruiters, onboarding, culture)",
      "Research team (analysts, researchers, writers)",
      "Creative agency (designers, copywriters, art directors)",
      "And more...",
    ],
    useCase: "Create any specialized team tailored to your unique business needs",
  },
]

export function DepartmentShowcase() {
  const [activeTab, setActiveTab] = useState(departments[0].id)
  const activeDept = departments.find((d) => d.id === activeTab)!

  return (
    <section className="py-24 bg-white">
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
            Your Autonomous AI Company
          </h2>
          <p className="text-2xl gradient-text font-semibold mb-4">
            Deploy Entire Departments in Minutes
          </p>
          <p className="text-xl text-[var(--body)] max-w-4xl mx-auto">
            Deviant isn't just another AI tool - it's a complete company of
            specialized AI agents that work together like real teams, with real
            hierarchy, real collaboration, and real output.
          </p>
        </motion.div>

        {/* Department tabs */}
        <div className="mb-12">
          <div className="flex flex-wrap justify-center gap-4">
            {departments.map((dept) => (
              <button
                key={dept.id}
                onClick={() => setActiveTab(dept.id)}
                className={`
                  px-6 py-3 rounded-lg font-semibold transition-all duration-300
                  flex items-center gap-2
                  ${
                    activeTab === dept.id
                      ? "bg-[var(--primary)] text-white shadow-lg"
                      : "bg-gray-100 text-[var(--body)] hover:bg-gray-200"
                  }
                `}
              >
                <dept.icon className="w-5 h-5" />
                <span className="hidden sm:inline">{dept.name}</span>
                <span className="sm:hidden">{dept.name.split(" ")[0]}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Department content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
          >
            <Card>
              <CardContent className="p-8 md:p-12">
                <div className="grid md:grid-cols-2 gap-12">
                  {/* Left side - Details */}
                  <div>
                    <div className="flex items-center gap-4 mb-6">
                      <div
                        className="w-16 h-16 rounded-xl flex items-center justify-center"
                        style={{
                          backgroundColor: `${activeDept.color}15`,
                        }}
                      >
                        <activeDept.icon
                          className="w-8 h-8"
                          style={{ color: activeDept.color }}
                        />
                      </div>
                      <h3 className="text-3xl font-bold">{activeDept.name}</h3>
                    </div>

                    <div className="mb-8">
                      <h4 className="text-lg font-semibold mb-4 text-[var(--heading)]">
                        Agents Included:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {activeDept.agents.map((agent) => (
                          <span
                            key={agent}
                            className="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium text-[var(--body)]"
                          >
                            {agent}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="mb-8">
                      <h4 className="text-lg font-semibold mb-4 text-[var(--heading)]">
                        What They Do:
                      </h4>
                      <ul className="space-y-3">
                        {activeDept.tasks.map((task, index) => (
                          <li
                            key={index}
                            className="flex items-start gap-3 text-[var(--body)]"
                          >
                            <div
                              className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0"
                              style={{ backgroundColor: activeDept.color }}
                            />
                            {task}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-6 bg-gradient-to-br from-[var(--primary)]/10 to-[var(--accent)]/10 rounded-xl">
                      <h4 className="text-lg font-semibold mb-2 text-[var(--heading)]">
                        Example Use Case:
                      </h4>
                      <p className="text-[var(--body)] font-medium">
                        "{activeDept.useCase}"
                      </p>
                    </div>
                  </div>

                  {/* Right side - Visual representation */}
                  <div className="flex items-center justify-center">
                    <div className="relative w-full max-w-md aspect-square">
                      {/* Org chart visualization */}
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ duration: 0.6 }}
                        className="space-y-6"
                      >
                        {/* Top level (Manager) */}
                        <div className="flex justify-center">
                          <motion.div
                            animate={{ y: [0, -5, 0] }}
                            transition={{
                              duration: 2,
                              repeat: Infinity,
                              ease: "easeInOut",
                            }}
                            className="px-6 py-3 rounded-lg text-white font-semibold shadow-lg"
                            style={{ backgroundColor: activeDept.color }}
                          >
                            {activeDept.agents[0]}
                          </motion.div>
                        </div>

                        {/* Connection lines */}
                        <div className="flex justify-center">
                          <div
                            className="w-0.5 h-8"
                            style={{ backgroundColor: `${activeDept.color}50` }}
                          />
                        </div>

                        {/* Team members */}
                        <div className="grid grid-cols-2 gap-4">
                          {activeDept.agents.slice(1, 5).map((agent, index) => (
                            <motion.div
                              key={agent}
                              animate={{ y: [0, -5, 0] }}
                              transition={{
                                duration: 2,
                                repeat: Infinity,
                                delay: index * 0.2,
                                ease: "easeInOut",
                              }}
                              className="px-4 py-2 rounded-lg bg-white border-2 text-sm font-medium text-center shadow"
                              style={{ borderColor: activeDept.color }}
                            >
                              {agent}
                            </motion.div>
                          ))}
                        </div>

                        {/* Activity indicators */}
                        <div className="flex justify-around mt-8">
                          {[0, 1, 2].map((i) => (
                            <motion.div
                              key={i}
                              animate={{
                                scale: [1, 1.2, 1],
                                opacity: [0.5, 1, 0.5],
                              }}
                              transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                delay: i * 0.5,
                              }}
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: activeDept.color }}
                            />
                          ))}
                        </div>
                      </motion.div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
