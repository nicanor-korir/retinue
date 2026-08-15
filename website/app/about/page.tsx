"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  Zap,
  Target,
  Globe,
  TrendingUp,
  Heart,
  Rocket,
  Eye,
  Shield,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Users,
} from "lucide-react"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function About() {
  const [activeAgent, setActiveAgent] = useState(0)

  const agents = [
    {
      name: "CEO Agent",
      role: "Chief Executive Officer",
      emoji: "👔",
      color: "var(--primary)",
      description: "Strategic oversight and project evaluation",
      responsibilities: [
        "Evaluates project viability",
        "Makes strategic decisions",
        "Final approvals on scope",
      ],
    },
    {
      name: "CTO Agent",
      role: "Chief Technology Officer",
      emoji: "🔧",
      color: "var(--accent)",
      description: "Technical architecture and code quality",
      responsibilities: [
        "Designs system architecture",
        "Reviews all code quality",
        "Ensures best practices",
      ],
    },
    {
      name: "PM Agent",
      role: "Project Manager",
      emoji: "📋",
      color: "var(--secondary)",
      description: "Task coordination and progress tracking",
      responsibilities: [
        "Breaks down requirements",
        "Assigns tasks to agents",
        "Tracks project progress",
      ],
    },
    {
      name: "HR Agent",
      role: "Human Resources",
      emoji: "👥",
      color: "var(--primary)",
      description: "System health and conflict resolution",
      responsibilities: [
        "Monitors agent health",
        "Resolves blockers",
        "Escalates critical issues",
      ],
    },
    {
      name: "Backend Engineer",
      role: "Senior Backend Engineer",
      emoji: "⚙️",
      color: "var(--accent)",
      description: "Server-side code and API development",
      responsibilities: [
        "Writes Python/FastAPI code",
        "Designs database schemas",
        "Creates REST APIs",
      ],
    },
    {
      name: "Frontend Engineer",
      role: "Senior Frontend Engineer",
      emoji: "💻",
      color: "var(--secondary)",
      description: "User interface and client code",
      responsibilities: [
        "Builds React components",
        "Implements responsive UI",
        "Ensures accessibility",
      ],
    },
    {
      name: "Designer Agent",
      role: "Product Designer",
      emoji: "🎨",
      color: "var(--primary)",
      description: "UI/UX specifications and design systems",
      responsibilities: [
        "Creates UI/UX specs",
        "Defines design systems",
        "Ensures user experience",
      ],
    },
  ]

  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section - Enhanced */}
      <section className="relative overflow-hidden pt-32 pb-20">
        {/* Animated background */}
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)]/5 via-transparent to-[var(--accent)]/5" />
        <div className="absolute inset-0">
          <div className="absolute top-20 left-20 w-72 h-72 bg-[var(--primary)]/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-[var(--accent)]/10 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-5xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--primary)]/10 rounded-full mb-6">
                <Sparkles className="w-4 h-4 text-[var(--primary)]" />
                <span className="text-sm font-semibold text-[var(--primary)]">
                  About Retinue
                </span>
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
                We're Building the
                <span className="block mt-2 bg-gradient-to-r from-[var(--primary)] via-[var(--accent)] to-[var(--secondary)] bg-clip-text text-transparent">
                  Future of Software
                </span>
              </h1>

              <p className="text-xl sm:text-2xl text-[var(--body)] mb-8 leading-relaxed max-w-3xl mx-auto">
                And the future is <strong className="text-[var(--heading)]">fully staffed</strong>.
                We're breaking every rule of traditional development to make
                software accessible to everyone, everywhere.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href="#story"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-[var(--secondary)] text-white rounded-lg font-semibold hover:bg-[var(--secondary-hover)] transition-all shadow-lg shadow-[var(--secondary)]/25 hover:shadow-xl hover:scale-105"
                >
                  Read Our Story
                  <ArrowRight className="w-5 h-5" />
                </a>
                <a
                  href="#team"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-[var(--primary)] text-[var(--primary)] rounded-lg font-semibold hover:bg-[var(--primary)]/5 transition-all"
                >
                  <Users className="w-5 h-5" />
                  Meet the AI Team
                </a>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-[var(--heading)] text-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-5xl mx-auto">
            {[
              { value: "100+", label: "Projects Built", icon: Rocket },
              { value: "1,200+", label: "Hours Saved", icon: Zap },
              { value: "$4.2M+", label: "Cost Savings", icon: TrendingUp },
              { value: "95%", label: "Satisfaction", icon: Heart },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="text-center"
              >
                <stat.icon className="w-8 h-8 mx-auto mb-3 text-[var(--secondary)]" />
                <div className="text-3xl sm:text-4xl font-bold mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Story Timeline */}
      <section id="story" className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              The Story Behind Retinue
            </h2>
            <p className="text-xl text-[var(--body)] max-w-2xl mx-auto">
              From watching talent die in Nairobi to building the world's first
              autonomous AI software company
            </p>
          </motion.div>

          <div className="space-y-12">
            {[
              {
                title: "The Problem",
                content:
                  "Brilliant entrepreneurs in Kenya were abandoning viable ideas because they couldn't afford developers. $50K-$120K development costs were killing innovation before it could start.",
                highlight: "Ideas died not from lack of viability, but lack of funds.",
              },
              {
                title: "The Realization",
                content:
                  "Software engineers spent 70% of their time coordinating, not coding. What if we could eliminate coordination entirely with autonomous AI agents?",
                highlight: "What if AI didn't assist developers - what if AI WAS the developers?",
              },
              {
                title: "The First Test",
                content:
                  "A complete todo application with authentication, CRUD operations, and modern UI. Traditional estimate: 1 week. Retinue agents: 4 hours. Production-ready. Deployed.",
                highlight: "Four hours. It worked.",
              },
              {
                title: "The Launch",
                content:
                  "November 16, 2025. Retinue went live. No massive marketing. Just a working product and a belief that the world needed a better way to build software.",
                highlight: "The response was immediate and polarizing. We focused on the believers.",
              },
            ].map((milestone, index) => (
              <motion.div
                key={milestone.title}
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2, duration: 0.6 }}
                className="relative pl-8 border-l-4 border-[var(--primary)]"
              >
                <div className="absolute -left-3 top-0 w-6 h-6 bg-[var(--primary)] rounded-full border-4 border-white shadow-lg" />
                <Card className="hover:shadow-xl transition-shadow">
                  <CardContent className="p-6">
                    <h3 className="text-2xl font-bold mb-3">{milestone.title}</h3>
                    <p className="text-[var(--body)] mb-4 leading-relaxed">
                      {milestone.content}
                    </p>
                    <blockquote className="border-l-4 border-[var(--secondary)] pl-4 italic text-[var(--heading)] font-medium">
                      "{milestone.highlight}"
                    </blockquote>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission & Vision - Redesigned */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <Card className="h-full bg-gradient-to-br from-[var(--primary)]/5 to-[var(--primary)]/10 border-2 border-[var(--primary)]/20 hover:border-[var(--primary)] transition-all">
                <CardContent className="p-10">
                  <div className="w-16 h-16 bg-[var(--primary)] rounded-2xl flex items-center justify-center mb-6 shadow-lg">
                    <Target className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-3xl font-bold mb-4">Our Mission</h3>
                  <p className="text-lg text-[var(--body)] leading-relaxed mb-6">
                    Build autonomous AI agents that develop software automatically -
                    eliminating human bottlenecks and democratizing access to
                    world-class development capabilities.
                  </p>
                  <div className="space-y-3">
                    {[
                      "Autonomous AI agents",
                      "Automatic development",
                      "Eliminate bottlenecks",
                      "Democratize access",
                    ].map((point) => (
                      <div key={point} className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-[var(--primary)] flex-shrink-0" />
                        <span className="text-[var(--body)] font-medium">{point}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <Card className="h-full bg-gradient-to-br from-[var(--accent)]/5 to-[var(--accent)]/10 border-2 border-[var(--accent)]/20 hover:border-[var(--accent)] transition-all">
                <CardContent className="p-10">
                  <div className="w-16 h-16 bg-[var(--accent)] rounded-2xl flex items-center justify-center mb-6 shadow-lg">
                    <Eye className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-3xl font-bold mb-4">Our Vision</h3>
                  <p className="text-lg text-[var(--body)] leading-relaxed mb-6">
                    A world where anyone can build software as easily as describing
                    it - where geographic and economic barriers to innovation
                    disappear.
                  </p>
                  <div className="space-y-3">
                    {[
                      "Equal access globally",
                      "Describe, don't code",
                      "Hours, not months",
                      "Hundreds, not thousands",
                    ].map((point) => (
                      <div key={point} className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-[var(--accent)] flex-shrink-0" />
                        <span className="text-[var(--body)] font-medium">{point}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Values - Redesigned Grid */}
      <section className="py-24 bg-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Core Values</h2>
            <p className="text-xl text-[var(--body)] max-w-2xl mx-auto">
              Principles that guide every decision we make
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Rocket,
                title: "Defiantly Different",
                description:
                  "We question best practices and break rules that deserve breaking. Different by design.",
                color: "var(--secondary)",
              },
              {
                icon: Eye,
                title: "Radically Transparent",
                description:
                  "Complete visibility into every decision and line of code. No black boxes, ever.",
                color: "var(--primary)",
              },
              {
                icon: Zap,
                title: "Relentlessly Autonomous",
                description:
                  "Zero human intervention required. Agents work 24/7, organizing and executing automatically.",
                color: "var(--accent)",
              },
              {
                icon: Globe,
                title: "Accessible by Default",
                description:
                  "World-class development for everyone, everywhere. Geography doesn't limit capability.",
                color: "var(--secondary)",
              },
              {
                icon: TrendingUp,
                title: "Speed Over Perfection",
                description:
                  "Ship fast, iterate faster. Perfect is the enemy of shipped. Hours, not weeks.",
                color: "var(--primary)",
              },
              {
                icon: Heart,
                title: "Human-First Automation",
                description:
                  "AI amplifies human potential, doesn't replace it. Humans strategize, AI executes.",
                color: "var(--accent)",
              },
            ].map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
              >
                <Card className="h-full group hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border-2 border-transparent hover:border-[var(--primary)]/20">
                  <CardContent className="p-8">
                    <div
                      className="w-14 h-14 rounded-xl flex items-center justify-center mb-5 shadow-lg group-hover:scale-110 transition-transform"
                      style={{ backgroundColor: value.color }}
                    >
                      <value.icon className="w-7 h-7 text-white" />
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-[var(--heading)]">
                      {value.title}
                    </h3>
                    <p className="text-[var(--body)] leading-relaxed">
                      {value.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* The 7 Agents - Interactive Showcase */}
      <section id="team" className="py-24 bg-gradient-to-b from-white to-gray-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Meet the Team: 7 Autonomous AI Agents
            </h2>
            <p className="text-xl text-[var(--body)] max-w-3xl mx-auto">
              Each agent is a specialized AI with distinct role, personality, and
              decision-making authority. They organize themselves, collaborate in
              real-time, and deliver production-ready software.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Agent Selection */}
            <div className="space-y-3">
              {agents.map((agent, index) => (
                <motion.button
                  key={agent.name}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => setActiveAgent(index)}
                  className={`w-full text-left p-6 rounded-xl transition-all ${
                    activeAgent === index
                      ? "bg-gradient-to-r from-[var(--primary)] to-[var(--accent)] text-white shadow-xl scale-105"
                      : "bg-white border-2 border-gray-200 hover:border-[var(--primary)] hover:shadow-lg"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="text-4xl">{agent.emoji}</div>
                    <div className="flex-1">
                      <h3
                        className={`text-lg font-bold mb-1 ${
                          activeAgent === index ? "text-white" : "text-[var(--heading)]"
                        }`}
                      >
                        {agent.name}
                      </h3>
                      <p
                        className={`text-sm ${
                          activeAgent === index
                            ? "text-white/90"
                            : "text-[var(--body)]"
                        }`}
                      >
                        {agent.role}
                      </p>
                    </div>
                    <CheckCircle2
                      className={`w-6 h-6 ${
                        activeAgent === index
                          ? "text-white"
                          : "text-gray-300"
                      }`}
                    />
                  </div>
                </motion.button>
              ))}
            </div>

            {/* Agent Details */}
            <motion.div
              key={activeAgent}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="h-full shadow-2xl border-2 border-[var(--primary)]/20">
                <CardContent className="p-10">
                  <div className="flex items-start gap-6 mb-6">
                    <div
                      className="text-6xl p-4 rounded-2xl shadow-lg"
                      style={{
                        backgroundColor: `${agents[activeAgent].color}15`,
                      }}
                    >
                      {agents[activeAgent].emoji}
                    </div>
                    <div>
                      <h3 className="text-3xl font-bold mb-2">
                        {agents[activeAgent].name}
                      </h3>
                      <p
                        className="text-lg font-semibold"
                        style={{ color: agents[activeAgent].color }}
                      >
                        {agents[activeAgent].role}
                      </p>
                    </div>
                  </div>

                  <p className="text-lg text-[var(--body)] mb-6 leading-relaxed">
                    {agents[activeAgent].description}
                  </p>

                  <div className="bg-gray-50 rounded-xl p-6">
                    <h4 className="font-bold text-[var(--heading)] mb-4">
                      Key Responsibilities:
                    </h4>
                    <ul className="space-y-3">
                      {agents[activeAgent].responsibilities.map((resp) => (
                        <li key={resp} className="flex items-start gap-3">
                          <div
                            className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                            style={{
                              backgroundColor: `${agents[activeAgent].color}15`,
                            }}
                          >
                            <CheckCircle2
                              className="w-4 h-4"
                              style={{ color: agents[activeAgent].color }}
                            />
                          </div>
                          <span className="text-[var(--body)]">{resp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-12"
          >
            <Card className="bg-gradient-to-br from-[var(--secondary)]/10 to-[var(--secondary)]/5 border-2 border-[var(--secondary)]/20">
              <CardContent className="p-8 text-center">
                <Sparkles className="w-12 h-12 mx-auto mb-4 text-[var(--secondary)]" />
                <p className="text-xl font-semibold text-[var(--heading)]">
                  This isn't a metaphor. These 7 agents are the actual team that
                  builds your software - autonomously, collaboratively, and
                  in real-time.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Founder Section - Enhanced */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">The Founder</h2>
            <p className="text-xl text-[var(--body)]">
              Building the future from Nairobi, Kenya
            </p>
          </motion.div>

          <Card className="shadow-2xl border-2 border-[var(--primary)]/20">
            <CardContent className="p-10">
              <div className="flex flex-col md:flex-row items-start gap-8">
                <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center text-white text-5xl font-bold shadow-xl flex-shrink-0">
                  NK
                </div>
                <div className="flex-1">
                  <h3 className="text-3xl font-bold mb-2">Nicanor Korir</h3>
                  <p className="text-xl text-[var(--primary)] font-semibold mb-4">
                    Founder & CEO
                  </p>
                  <p className="text-[var(--body)] leading-relaxed mb-6">
                    Senior software engineer and AI specialist with a master's
                    degree in Artificial Intelligence. Built Retinue after watching
                    too many brilliant entrepreneurs abandon viable ideas because
                    they couldn't afford developers.
                  </p>

                  <blockquote className="border-l-4 border-[var(--secondary)] pl-6 py-2 mb-6 italic text-lg">
                    "I realized we didn't need to make development 20% faster. We
                    needed to make it 100x more accessible. That required breaking
                    the model entirely."
                  </blockquote>

                  <div className="grid sm:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-bold text-[var(--heading)] mb-3">
                        Education
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="text-[var(--body)]">
                          • Master's in AI
                        </p>
                        <p className="text-[var(--body)]">
                          • Bachelor's in Software Engineering
                        </p>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-bold text-[var(--heading)] mb-3">
                        Expertise
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {["AI/ML", "Multi-agent Systems", "Full-stack"].map(
                          (skill) => (
                            <span
                              key={skill}
                              className="px-3 py-1 bg-[var(--primary)]/10 text-[var(--primary)] rounded-full text-xs font-medium"
                            >
                              {skill}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section - Enhanced */}
      <section className="py-24 bg-gradient-to-br from-[var(--heading)] via-[var(--heading)] to-[var(--primary)]/20 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,.05)_50%,transparent_75%,transparent_100%)] bg-[length:250px_250px] animate-[slide_20s_linear_infinite]" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <Sparkles className="w-16 h-16 mx-auto mb-6 text-[var(--secondary)]" />
            <h2 className="text-4xl sm:text-5xl font-bold mb-6">
              Join the Deviation
            </h2>
            <p className="text-xl text-gray-300 mb-10 max-w-2xl mx-auto leading-relaxed">
              If you believe software development can be better, that innovation
              shouldn't require Silicon Valley budgets, and that AI should be
              transparent - you're already one of us.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link href="/#waitlist">
                <Button
                  variant="primary"
                  size="lg"
                  className="group bg-[var(--secondary)] hover:bg-[var(--secondary-hover)]"
                >
                  Start Building
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link href="/press-kit">
                <Button
                  variant="outline"
                  size="lg"
                  className="border-white text-white hover:bg-white/10"
                >
                  Press Kit
                </Button>
              </Link>
            </div>

            <Card className="bg-white/10 backdrop-blur-sm border-white/20">
              <CardContent className="p-8">
                <h3 className="text-2xl font-bold mb-6">Contact Us</h3>
                <div className="grid sm:grid-cols-2 gap-6 text-left">
                  <div>
                    <h4 className="font-semibold mb-3 text-white">General</h4>
                    <div className="space-y-2 text-sm">
                      <p className="text-gray-300">
                        <a
                          href="mailto:hello@retinue.team"
                          className="hover:text-[var(--secondary)] transition-colors"
                        >
                          hello@retinue.team
                        </a>
                      </p>
                      <p className="text-gray-300">
                        <a
                          href="mailto:support@retinue.team"
                          className="hover:text-[var(--secondary)] transition-colors"
                        >
                          support@retinue.team
                        </a>
                      </p>
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-3 text-white">Business</h4>
                    <div className="space-y-2 text-sm">
                      <p className="text-gray-300">
                        <a
                          href="mailto:press@retinue.team"
                          className="hover:text-[var(--secondary)] transition-colors"
                        >
                          press@retinue.team
                        </a>
                      </p>
                      <p className="text-gray-300">
                        <a
                          href="mailto:partnerships@retinue.team"
                          className="hover:text-[var(--secondary)] transition-colors"
                        >
                          partnerships@retinue.team
                        </a>
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-6 pt-6 border-t border-white/20">
                  <p className="text-gray-300">
                    <Globe className="w-4 h-4 inline mr-2" />
                    Nairobi, Kenya • Global Operations
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>
    </main>
  )
}
