"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Lock, Zap, Gift, CheckCircle2, Loader2, Rocket } from "lucide-react"
import { LaunchCountdown } from "@/components/launch/LaunchCountdown"
import { useLaunchCountdown } from "@/components/launch/useLaunchCountdown"
import { LAUNCH_CONFIG } from "@/components/launch/launchConfig"

const waitlistSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  fullName: z.string().min(2, "Please enter your full name"),
  companyName: z.string().optional(),
  useCase: z.string().min(1, "Please select a use case"),
  companySize: z.string().optional(),
  betaTester: z.boolean().optional(),
  updates: z.boolean().optional(),
})

type WaitlistForm = z.infer<typeof waitlistSchema>

export function FinalCTA() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const { isCountdownActive, launchPhase } = useLaunchCountdown()
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<WaitlistForm>({
    resolver: zodResolver(waitlistSchema),
    defaultValues: {
      betaTester: false,
      updates: true,
    },
  })

  const onSubmit = async (data: WaitlistForm) => {
    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      })

      const result = await response.json()

      if (response.ok) {
        setIsSubmitted(true)
        reset()
      } else {
        setSubmitError(result.message || "Something went wrong. Please try again.")
      }
    } catch (error) {
      console.error("Error submitting form:", error)
      setSubmitError("Unable to connect. Please check your internet connection and try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section id="waitlist" className="py-24 bg-gradient-to-br from-[var(--primary)]/10 via-white to-[var(--accent)]/10 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[var(--primary)]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[var(--accent)]/10 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          {/* Launch Countdown Widget */}
          {isCountdownActive && LAUNCH_CONFIG.features.showCountdownInCTA && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="mb-10"
            >
              <div className="max-w-4xl mx-auto bg-gradient-to-r from-[var(--primary)] via-[var(--accent)] to-[var(--secondary)] rounded-2xl p-8 relative overflow-hidden">
                {/* Background pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute inset-0" style={{
                    backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
                    backgroundSize: '40px 40px'
                  }} />
                </div>

                <div className="relative z-10">
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <Rocket className="w-6 h-6 text-white" />
                    <h3 className="text-2xl sm:text-3xl font-bold text-white">
                      Launch Day Countdown
                    </h3>
                  </div>
                  <p className="text-white/90 text-base sm:text-lg mb-6">
                    Reserve your spot before December 22nd, 2025
                  </p>
                  <LaunchCountdown variant="compact" />
                </div>
              </div>
            </motion.div>
          )}

          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4">
            {isCountdownActive ? 'Reserve Your Launch Day Access' : 'Build Your AI Company Today'}
          </h2>
          <p className="text-xl sm:text-2xl text-[var(--body)] mb-6">
            Join 500+ forward-thinking companies on the waitlist
          </p>
          <div className="max-w-3xl mx-auto bg-gradient-to-r from-[var(--secondary)]/10 via-[var(--primary)]/10 to-[var(--accent)]/10 rounded-2xl p-6 mb-8 border border-[var(--primary)]/20">
            <h3 className="text-2xl font-bold mb-4 text-[var(--heading)]">
              {isCountdownActive ? '🎯 Lock In Your Launch Day Benefits' : '🚀 Early Adopter Exclusive Benefits'}
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-left">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[var(--primary)] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[var(--heading)]">50% Off for 6 Months</p>
                  <p className="text-sm text-[var(--body)]">Lock in early adopter pricing</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[var(--primary)] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[var(--heading)]">Direct Founder Access</p>
                  <p className="text-sm text-[var(--body)]">Chat directly with our founder about your challenges</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[var(--primary)] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[var(--heading)]">Priority Rollout</p>
                  <p className="text-sm text-[var(--body)]">Be among the first to access Deviant</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[var(--primary)] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[var(--heading)]">Shape the Product</p>
                  <p className="text-sm text-[var(--body)]">Your feedback directly influences our roadmap</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Waitlist form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="max-w-2xl mx-auto"
        >
          <Card className="shadow-2xl">
            <CardContent className="p-8">
              {!isSubmitted ? (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  {/* Email */}
                  <div>
                    <Label htmlFor="email">
                      Email Address <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@company.com"
                      {...register("email")}
                      className="mt-2"
                    />
                    {errors.email && (
                      <p className="text-red-500 text-sm mt-1">
                        {errors.email.message}
                      </p>
                    )}
                  </div>

                  {/* Full Name */}
                  <div>
                    <Label htmlFor="fullName">
                      Full Name <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="fullName"
                      type="text"
                      placeholder="John Doe"
                      {...register("fullName")}
                      className="mt-2"
                    />
                    {errors.fullName && (
                      <p className="text-red-500 text-sm mt-1">
                        {errors.fullName.message}
                      </p>
                    )}
                  </div>

                  {/* Company Name */}
                  <div>
                    <Label htmlFor="companyName">Company Name (Optional)</Label>
                    <Input
                      id="companyName"
                      type="text"
                      placeholder="Acme Inc."
                      {...register("companyName")}
                      className="mt-2"
                    />
                  </div>

                  {/* Use Case */}
                  <div>
                    <Label htmlFor="useCase">
                      Primary Use Case <span className="text-red-500">*</span>
                    </Label>
                    <Select
                      id="useCase"
                      {...register("useCase")}
                      className="mt-2"
                    >
                      <option value="">Select a use case</option>
                      <option value="software-development">
                        Software Development
                      </option>
                      <option value="marketing-growth">
                        Marketing & Growth
                      </option>
                      <option value="sales-business-dev">
                        Sales & Business Development
                      </option>
                      <option value="operations-finance">
                        Operations & Finance
                      </option>
                      <option value="custom-other">Custom/Other</option>
                    </Select>
                    {errors.useCase && (
                      <p className="text-red-500 text-sm mt-1">
                        {errors.useCase.message}
                      </p>
                    )}
                  </div>

                  {/* Company Size */}
                  <div>
                    <Label htmlFor="companySize">Company Size (Optional)</Label>
                    <Select
                      id="companySize"
                      {...register("companySize")}
                      className="mt-2"
                    >
                      <option value="">Select company size</option>
                      <option value="solo">Solo</option>
                      <option value="2-10">2-10</option>
                      <option value="11-50">11-50</option>
                      <option value="51-200">51-200</option>
                      <option value="200+">200+</option>
                    </Select>
                  </div>

                  {/* Checkboxes */}
                  <div className="space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        {...register("betaTester")}
                        className="mt-1 w-5 h-5 text-[var(--primary)] border-gray-300 rounded focus:ring-[var(--primary)]"
                      />
                      <span className="text-[var(--body)]">
                        I want to participate in beta testing
                      </span>
                    </label>

                    <label className="flex items-start gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        {...register("updates")}
                        defaultChecked
                        className="mt-1 w-5 h-5 text-[var(--primary)] border-gray-300 rounded focus:ring-[var(--primary)]"
                      />
                      <span className="text-[var(--body)]">
                        Send me updates on Deviant development
                      </span>
                    </label>
                  </div>

                  {/* Error Message */}
                  {submitError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-red-600 text-sm">{submitError}</p>
                    </div>
                  )}

                  {/* Submit button */}
                  <Button
                    type="submit"
                    size="lg"
                    className="w-full"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 w-5 h-5 animate-spin" />
                        Reserving Your Spot...
                      </>
                    ) : (
                      isCountdownActive ? "Reserve My Launch Day Spot" : "Join the Waitlist"
                    )}
                  </Button>

                  {/* Trust indicators */}
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-4 text-sm text-[var(--muted)] pt-4">
                    <div className="flex items-center gap-2">
                      <Lock className="w-4 h-4" />
                      <span>We respect your privacy. No spam, ever.</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      <span>Get notified first when we launch</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Gift className="w-4 h-4" />
                      <span>Early adopters get 50% off</span>
                    </div>
                  </div>
                </form>
              ) : (
                <div className="text-center py-12">
                  <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <CheckCircle2 className="w-12 h-12 text-green-600" />
                  </div>
                  <h3 className="text-3xl font-bold mb-4">
                    You're on the list!
                  </h3>
                  <p className="text-xl text-[var(--body)] mb-8">
                    We'll notify you as soon as Deviant is ready for you.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  )
}
