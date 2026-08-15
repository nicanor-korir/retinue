"use client"

import { motion } from "framer-motion"
import { ArrowLeft, Download, Mail } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

export default function PressKit() {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-[var(--primary)]/10 via-white to-[var(--accent)]/10 py-20 pt-32">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              Retinue Press Kit
            </h1>
            <p className="text-xl text-[var(--body)] max-w-3xl mb-8">
              Media resources, company information, and assets for journalists
              and content creators.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button variant="primary" size="lg">
                <Download className="mr-2 w-5 h-5" />
                Download Media Kit
              </Button>
              <a
                href="mailto:press@retinue.team"
                className="inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 border-2 border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--primary)]/10 px-8 py-4 text-lg"
              >
                <Mail className="mr-2 w-5 h-5" />
                Contact Press Team
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Table of Contents */}
      <section className="bg-gray-50 py-12 border-b">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold mb-6">Table of Contents</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { id: "overview", title: "Company Overview" },
              { id: "story", title: "The Story" },
              { id: "product", title: "Product Description" },
              { id: "facts", title: "Key Facts & Statistics" },
              { id: "founder", title: "Founder Bio" },
              { id: "releases", title: "Press Releases" },
              { id: "assets", title: "Media Assets" },
              { id: "cases", title: "Use Cases" },
              { id: "quotes", title: "Quotes & Soundbites" },
              { id: "faq", title: "Press FAQs" },
              { id: "contact", title: "Contact Information" },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-left px-4 py-3 bg-white rounded-lg border border-gray-200 hover:border-[var(--primary)] hover:bg-[var(--primary)]/5 transition-all"
              >
                <span className="font-medium text-[var(--heading)]">
                  {item.title}
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Content */}
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16 max-w-5xl">
        {/* Company Overview */}
        <section id="overview" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">Company Overview</h2>

          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">
                  Short Boilerplate (50 words)
                </h3>
                <p className="text-[var(--body)] leading-relaxed">
                  Retinue is an autonomous AI software company that builds
                  custom applications automatically. Using 7 specialized AI
                  agents that function as CEO, CTO, engineers, and designers,
                  Retinue delivers in hours what traditional development takes
                  weeks to build - at a fraction of the cost.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">
                  Medium Boilerplate (100 words)
                </h3>
                <p className="text-[var(--body)] leading-relaxed">
                  Retinue is revolutionizing software development through
                  autonomous AI agents. Our platform features 7 specialized AI
                  agents (CEO, CTO, Project Manager, HR, Backend Engineer,
                  Frontend Engineer, and Designer) that organize themselves,
                  make decisions, write code, and deploy applications -
                  automatically. What takes traditional development teams weeks
                  or months, Retinue delivers in hours. Founded in Kenya and
                  serving customers globally, Retinue democratizes access to
                  world-class software development, making enterprise-level
                  capabilities accessible to entrepreneurs, small businesses,
                  and organizations worldwide.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">
                  Long Boilerplate (200 words)
                </h3>
                <p className="text-[var(--body)] leading-relaxed mb-4">
                  Retinue is pioneering the future of software development
                  through fully autonomous AI agents. Unlike traditional AI
                  coding assistants that help developers work faster, Retinue
                  replaces the entire development team with 7 specialized AI
                  agents that function as a complete software company.
                </p>
                <p className="text-[var(--body)] leading-relaxed mb-4">
                  Each agent has a distinct role: the CEO Agent evaluates
                  projects and makes strategic decisions, the CTO Agent provides
                  technical guidance and reviews code, the Project Manager
                  breaks down requirements into tasks, the HR Agent monitors
                  system health, and three engineering agents (Backend,
                  Frontend, Designer) write production-ready code and create
                  professional designs.
                </p>
                <p className="text-[var(--body)] leading-relaxed">
                  Founded in Kenya by entrepreneur and AI engineer Nicanor
                  Korir, Retinue addresses a critical global problem: quality
                  software development is too expensive and too slow for most
                  businesses. By automating the entire development process,
                  Retinue makes enterprise-level software accessible to
                  entrepreneurs, small businesses, and organizations worldwide -
                  regardless of budget or location.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* The Story */}
        <section id="story" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">The Story</h2>

          <div className="prose prose-lg max-w-none">
            <h3 className="text-2xl font-semibold mb-4">Origin Story</h3>
            <blockquote className="border-l-4 border-[var(--primary)] pl-6 italic text-xl mb-6">
              "What if you could describe what you need and have it built
              automatically?"
            </blockquote>

            <p className="text-[var(--body)] leading-relaxed mb-6">
              Nicanor Korir, a senior software engineer and AI specialist from
              Kenya, spent years watching talented entrepreneurs with brilliant
              ideas fail because they couldn't afford developers. The
              traditional model was broken: hire developers ($80K+/year), manage
              them (weeks of coordination), and wait months for results.
            </p>

            <p className="text-[var(--body)] leading-relaxed mb-6">
              "I saw founders in Nairobi with ideas that could serve millions,
              but they needed $50,000 and 6 months just to validate those
              ideas," Nicanor explains. "Meanwhile, AI was getting powerful
              enough to write code, design interfaces, and make decisions. I
              realized we didn't need AI to help developers - we needed AI to BE
              the developers."
            </p>

            <p className="text-[var(--body)] leading-relaxed mb-6">
              In October 2025, after months of research and development, Nicanor
              launched Retinue: a complete AI software company where 7
              autonomous agents collaborate to build applications automatically.
              The first test project - a complete todo application with
              authentication, database, and modern UI - took the system just 4
              hours to build.
            </p>

            <p className="text-[var(--body)] leading-relaxed font-semibold">
              The name "Retinue" reflects the philosophy: a retinue is the
              hand-picked company of specialists who accompany someone with
              something to accomplish. Every founder deserves one.
            </p>
          </div>
        </section>

        {/* Key Facts */}
        <section id="facts" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">Key Facts & Statistics</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">Company Facts</h3>
                <ul className="space-y-2 text-[var(--body)]">
                  <li>
                    <strong>Founded:</strong> October 2025
                  </li>
                  <li>
                    <strong>Headquarters:</strong> Nairobi, Kenya
                  </li>
                  <li>
                    <strong>Founder:</strong> Nicanor Korir
                  </li>
                  <li>
                    <strong>Industry:</strong> AI, Software Development, SaaS
                  </li>
                  <li>
                    <strong>Stage:</strong> Pre-Seed MVP
                  </li>
                  <li>
                    <strong>Website:</strong> retinue.team
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">
                  Product Statistics
                </h3>
                <ul className="space-y-2 text-[var(--body)]">
                  <li>
                    <strong>AI Agents:</strong> 7 specialized agents
                  </li>
                  <li>
                    <strong>Build Time:</strong> 4-18 hours
                  </li>
                  <li>
                    <strong>Cost Reduction:</strong> 90-98%
                  </li>
                  <li>
                    <strong>Speed:</strong> 10-100x faster
                  </li>
                  <li>
                    <strong>Languages:</strong> Python, JavaScript, TypeScript
                  </li>
                  <li>
                    <strong>Response Time:</strong> &lt;100ms
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">Market Impact</h3>
                <ul className="space-y-2 text-[var(--body)]">
                  <li>
                    <strong>Traditional MVP Cost:</strong> $50K - $150K
                  </li>
                  <li>
                    <strong>Retinue MVP Cost:</strong> $800 - $2,000
                  </li>
                  <li>
                    <strong>Traditional Timeline:</strong> 3-6 months
                  </li>
                  <li>
                    <strong>Retinue Timeline:</strong> 4-18 hours
                  </li>
                  <li>
                    <strong>Target Market:</strong> 30M+ entrepreneurs globally
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">The 7 Agents</h3>
                <ul className="space-y-2 text-[var(--body)]">
                  <li>
                    <strong>CEO:</strong> Strategic decisions
                  </li>
                  <li>
                    <strong>CTO:</strong> Technical architecture
                  </li>
                  <li>
                    <strong>PM:</strong> Task coordination
                  </li>
                  <li>
                    <strong>HR:</strong> System monitoring
                  </li>
                  <li>
                    <strong>Backend:</strong> Server code
                  </li>
                  <li>
                    <strong>Frontend:</strong> User interface
                  </li>
                  <li>
                    <strong>Designer:</strong> UI/UX specs
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Founder Bio */}
        <section id="founder" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">Founder Bio</h2>

          <Card>
            <CardContent className="p-8">
              <h3 className="text-2xl font-semibold mb-6">
                Nicanor Korir - Founder & CEO
              </h3>

              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-lg mb-2">
                    Short Bio (50 words):
                  </h4>
                  <p className="text-[var(--body)] leading-relaxed">
                    Nicanor Korir is a Kenyan entrepreneur and senior software
                    engineer with a master's degree in AI. He founded Retinue to
                    democratize software development globally, making
                    enterprise-level development accessible to entrepreneurs
                    everywhere through autonomous AI agents.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-lg mb-2">
                    Medium Bio (150 words):
                  </h4>
                  <p className="text-[var(--body)] leading-relaxed">
                    Nicanor Korir is the founder and CEO of Retinue, an
                    autonomous AI software company based in Nairobi, Kenya. A
                    senior software engineer with a master's degree in
                    Artificial Intelligence, Nicanor has spent his career at the
                    intersection of AI/ML and practical software development.
                    Before founding Retinue, Nicanor witnessed countless
                    talented African entrepreneurs abandon viable business ideas
                    because custom software development was too expensive and
                    too slow. This inspired him to build a solution: autonomous
                    AI agents that function as a complete software company,
                    delivering in hours what traditional teams take weeks to
                    build. Nicanor is passionate about using AI to solve
                    Africa-specific problems while building globally scalable
                    solutions.
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-lg mb-2">Expertise:</h4>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "AI/ML Engineering",
                      "Multi-agent Systems",
                      "Full-stack Development",
                      "Voice Synthesis & NLP",
                      "SaaS Architecture",
                      "African Market Solutions",
                    ].map((skill) => (
                      <span
                        key={skill}
                        className="px-3 py-1 bg-[var(--primary)]/10 text-[var(--primary)] rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Quotes */}
        <section id="quotes" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">Quotes & Soundbites</h2>

          <div className="space-y-6">
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4">On the problem:</h3>
                <blockquote className="border-l-4 border-[var(--primary)] pl-6 italic text-lg text-[var(--body)]">
                  "Traditional software development is broken. It's too
                  expensive, too slow, and too inaccessible. We built Retinue to
                  prove there's a better way."
                </blockquote>
                <p className="text-sm text-[var(--muted)] mt-2">
                  - Nicanor Korir, Founder & CEO
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4">On the vision:</h3>
                <blockquote className="border-l-4 border-[var(--primary)] pl-6 italic text-lg text-[var(--body)]">
                  "We envision a world where anyone can build software as easily
                  as describing it. A founder in Nairobi should have the same
                  development capabilities as a funded Silicon Valley startup."
                </blockquote>
                <p className="text-sm text-[var(--muted)] mt-2">
                  - Nicanor Korir, Founder & CEO
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4">
                  On accessibility:
                </h3>
                <blockquote className="border-l-4 border-[var(--primary)] pl-6 italic text-lg text-[var(--body)]">
                  "Quality software development has been accessible only to the
                  wealthy. Retinue democratizes it - making enterprise-level
                  development available to everyone, everywhere."
                </blockquote>
                <p className="text-sm text-[var(--muted)] mt-2">
                  - Nicanor Korir, Founder & CEO
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-4">On building differently:</h3>
                <blockquote className="border-l-4 border-[var(--primary)] pl-6 italic text-lg text-[var(--body)]">
                  "We give every founder a retinue - a full company of
                  specialists, hand-picked per project. We break every rule of
                  traditional development, and we deliver better results because of it."
                </blockquote>
                <p className="text-sm text-[var(--muted)] mt-2">
                  - Nicanor Korir, Founder & CEO
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Contact */}
        <section id="contact" className="mb-20 scroll-mt-24">
          <h2 className="text-3xl font-bold mb-8">Contact Information</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">Press Inquiries</h3>
                <div className="space-y-3 text-[var(--body)]">
                  <p>
                    <strong>Email:</strong>{" "}
                    <a
                      href="mailto:press@retinue.team"
                      className="text-[var(--primary)] hover:underline"
                    >
                      press@retinue.team
                    </a>
                  </p>
                  <p>
                    <strong>Website:</strong>{" "}
                    <a
                      href="https://retinue.team"
                      className="text-[var(--primary)] hover:underline"
                    >
                      retinue.team
                    </a>
                  </p>
                  <p>
                    <strong>Response Time:</strong> Within 24 hours
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h3 className="text-xl font-semibold mb-4">General Contact</h3>
                <div className="space-y-3 text-[var(--body)]">
                  <p>
                    <strong>Business:</strong>{" "}
                    <a
                      href="mailto:hello@retinue.team"
                      className="text-[var(--primary)] hover:underline"
                    >
                      hello@retinue.team
                    </a>
                  </p>
                  <p>
                    <strong>Support:</strong>{" "}
                    <a
                      href="mailto:support@retinue.team"
                      className="text-[var(--primary)] hover:underline"
                    >
                      support@retinue.team
                    </a>
                  </p>
                  <p>
                    <strong>Partnerships:</strong>{" "}
                    <a
                      href="mailto:partnerships@retinue.team"
                      className="text-[var(--primary)] hover:underline"
                    >
                      partnerships@retinue.team
                    </a>
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6 bg-gradient-to-br from-[var(--primary)]/10 to-[var(--accent)]/10 border-[var(--primary)]/20">
            <CardContent className="p-8 text-center">
              <h3 className="text-2xl font-semibold mb-4">
                Need Additional Resources?
              </h3>
              <p className="text-[var(--body)] mb-6 max-w-2xl mx-auto">
                Media can request demo access, high-resolution images, video
                assets, or schedule interviews with our founder.
              </p>
              <a
                href="mailto:press@retinue.team?subject=Press Kit Request"
                className="inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 bg-[var(--secondary)] text-white hover:bg-[var(--secondary-hover)] shadow-lg shadow-[var(--secondary)]/25 hover:shadow-xl hover:shadow-[var(--secondary)]/30 transform hover:scale-105 px-8 py-4 text-lg"
              >
                <Mail className="mr-2 w-5 h-5" />
                Request Media Resources
              </a>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  )
}
