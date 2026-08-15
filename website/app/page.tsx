"use client"

import { Hero } from "@/components/sections/Hero"
import { ProblemStatement } from "@/components/sections/ProblemStatement"
import { DepartmentShowcase } from "@/components/sections/DepartmentShowcase"
import { HowItWorks } from "@/components/sections/HowItWorks"
import { Features } from "@/components/sections/Features"
import { UseCases } from "@/components/sections/UseCases"
import { Pricing } from "@/components/sections/Pricing"
import { FAQ } from "@/components/sections/FAQ"
import { FinalCTA } from "@/components/sections/FinalCTA"
import { Footer } from "@/components/sections/Footer"
import { LaunchModal } from "@/components/launch/LaunchModal"
import { LaunchCelebration } from "@/components/launch/LaunchCelebration"

export default function Home() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <main className="min-h-screen">
      <Hero />
      <ProblemStatement />
      <DepartmentShowcase />
      <HowItWorks />
      <Features />
      <UseCases />
      <Pricing />
      <FAQ />
      <FinalCTA />

      {/* Launch Modal - shows on first visit */}
      <LaunchModal onJoinWaitlist={() => scrollToSection('waitlist')} />

      {/* Launch Celebration - confetti on launch day */}
      <LaunchCelebration />
    </main>
  )
}
