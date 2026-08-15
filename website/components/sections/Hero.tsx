"use client"

import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ArrowRight, Play, Sparkles, Zap } from "lucide-react"

export function Hero() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-white via-[var(--primary)]/5 to-white pt-16 md:pt-20">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[var(--primary)]/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[var(--accent)]/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left side - Text content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center lg:text-left"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--primary)]/10 text-[var(--primary)] text-sm font-medium mb-6"
            >
              <Sparkles className="w-4 h-4" />
              <span>Retinue Built Our Stack Differently</span>
            </motion.div>

            {/* Main headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
            >
              Build Business Solutions {" "}
              <span className="gradient-text">with an Autonomous TEAM</span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-lg sm:text-2xl text-[var(--body)] py-2 mb-8 max-w-2xl mx-auto lg:mx-0"
            >
              Autonomous AI agents that develop business solutions with you.
              From idea to ready solutions in <strong>minutes</strong> while working with a team like a boardroom.
            </motion.p>

            {/* CTAs */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
            >
              <Button
                size="lg"
                className="group"
                onClick={() => scrollToSection('waitlist')}
              >
                Join the Waitlist
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="group"
                onClick={() => scrollToSection('how-it-works')}
              >
                <Play className="mr-2 w-5 h-5" />
                See How It Works
              </Button>
            </motion.div>

            {/* Social proof strip */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="mt-12 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-6 sm:gap-8 text-sm text-[var(--muted)]"
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-[var(--primary)] rounded-full" />
                <span>Autonomous • Transparent • Fast</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-[var(--accent)] rounded-full" />
                <span>Built in Hours, Not Months</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-[var(--secondary)] rounded-full" />
                <span>Save 90%+ on Development</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Right side - Enhanced Animated visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="relative hidden lg:block"
          >
            {/* Central hub */}
            <div className="relative w-full aspect-square max-w-lg mx-auto">
              {/* Center node - You */}
              <motion.div
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="absolute top-3/8 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-28 h-28 bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] rounded-full shadow-2xl flex items-center justify-center text-white font-bold z-20 text-lg border-4 border-white"
              >
                You
              </motion.div>

              {/* AI Agent nodes with enhanced spacing and collaboration */}
              {[
                { name: "CTO", angle: 51, color: "var(--accent)", icon: "🔧" },
                { name: "PM", angle: 102, color: "var(--secondary)", icon: "📋" },
                { name: "Backend", angle: 153, color: "var(--primary)", icon: "⚙️" },
                { name: "Frontend", angle: 204, color: "var(--accent)", icon: "💻" },
                { name: "Designer", angle: 255, color: "var(--secondary)", icon: "🎨" },
                { name: "HR", angle: 306, color: "var(--primary)", icon: "👥" },
                { name: "CEO", angle: 0, color: "var(--primary)", icon: "👔" },
              ].map((dept, index) => {
                const radius = 200 // Increased radius for more spacing
                const x = Math.cos((dept.angle * Math.PI) / 180) * radius
                const y = Math.sin((dept.angle * Math.PI) / 180) * radius

                return (
                  <motion.div
                    key={dept.name}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="absolute top-1/2 left-1/2"
                    style={{
                      transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                    }}
                  >
                    {/* Connection line to center */}
                    <motion.div
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ delay: 0.8 + index * 0.1 }}
                      className="absolute h-0.5 bg-gradient-to-r from-[var(--primary)]/40 to-transparent"
                      style={{
                        width: `${radius}px`,
                        transformOrigin: "left center",
                        transform: `rotate(${dept.angle + 180}deg)`,
                        left: "50%",
                        top: "50%",
                      }}
                    />

                    {/* Data flow animation - particles moving along the line */}
                    <motion.div
                      animate={{
                        x: [0, -radius],
                        opacity: [0, 1, 1, 0],
                      }}
                      transition={{
                        duration: 2.5,
                        repeat: Infinity,
                        delay: index * 0.4,
                        ease: "linear",
                      }}
                      className="absolute w-2 h-2 rounded-full bg-[var(--secondary)]"
                      style={{
                        left: "50%",
                        top: "50%",
                        transform: `rotate(${dept.angle + 180}deg)`,
                      }}
                    />

                    {/* Department node */}
                    <motion.div
                      animate={{
                        y: [0, -12, 0],
                      }}
                      transition={{
                        duration: 2.5,
                        repeat: Infinity,
                        delay: index * 0.3,
                        ease: "easeInOut",
                      }}
                      className="relative"
                    >
                      <div
                        className="w-20 h-20 rounded-xl shadow-xl flex flex-col items-center justify-center text-white text-xs font-semibold backdrop-blur-sm border-2 border-white/20"
                        style={{ backgroundColor: dept.color }}
                      >
                        <span className="text-2xl mb-1">{dept.icon}</span>
                        <span>{dept.name}</span>
                      </div>

                      {/* Activity indicator */}
                      <motion.div
                        animate={{ scale: [1, 1.3, 1], opacity: [0.6, 1, 0.6] }}
                        transition={{
                          duration: 1.8,
                          repeat: Infinity,
                          delay: index * 0.3,
                        }}
                        className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full shadow-lg"
                      >
                        <motion.div
                          animate={{ scale: [1, 1.5, 1], opacity: [0.8, 0, 0.8] }}
                          transition={{
                            duration: 1.8,
                            repeat: Infinity,
                            delay: index * 0.3,
                          }}
                          className="absolute inset-0 bg-green-400 rounded-full"
                        />
                      </motion.div>

                      {/* Work indicator - pulsing icon */}
                      <motion.div
                        animate={{
                          scale: [1, 1.2, 1],
                          rotate: [0, 10, -10, 0]
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          delay: index * 0.5,
                        }}
                        className="absolute -bottom-2 -left-2 w-6 h-6 bg-white rounded-full shadow-md flex items-center justify-center"
                      >
                        <Zap className="w-3 h-3 text-[var(--secondary)]" />
                      </motion.div>
                    </motion.div>
                  </motion.div>
                )
              })}

              {/* Collaboration lines between agents (adjacent connections) */}
              {[0, 1, 2, 3, 4, 5, 6].map((index) => {
                const nextIndex = (index + 1) % 7
                const angles = [0, 51, 102, 153, 204, 255, 306]
                const angle1 = angles[index]
                const angle2 = angles[nextIndex]
                const radius = 200
                const x1 = Math.cos((angle1 * Math.PI) / 180) * radius
                const y1 = Math.sin((angle1 * Math.PI) / 180) * radius
                const x2 = Math.cos((angle2 * Math.PI) / 180) * radius
                const y2 = Math.sin((angle2 * Math.PI) / 180) * radius

                const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2))
                const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI)

                return (
                  <motion.div
                    key={`collab-${index}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0, 0.3, 0] }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      delay: index * 0.5,
                    }}
                    className="absolute top-1/2 left-1/2"
                    style={{
                      width: `${length}px`,
                      height: '2px',
                      background: 'linear-gradient(90deg, var(--accent), var(--primary))',
                      transformOrigin: 'left center',
                      transform: `translate(${x1}px, ${y1}px) rotate(${angle}deg)`,
                    }}
                  />
                )
              })}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2 cursor-pointer"
        onClick={() => scrollToSection('problem')}
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-6 h-10 border-2 border-[var(--primary)] rounded-full flex items-start justify-center p-2"
        >
          <motion.div
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 bg-[var(--primary)] rounded-full"
          />
        </motion.div>
      </motion.div>
    </section>
  )
}
