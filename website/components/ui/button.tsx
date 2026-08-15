import * as React from "react"
import { cn } from "@/libs/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost"
  size?: "sm" | "md" | "lg"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          {
            // Primary CTA - High converting orange (research shows 21-31% better conversion)
            "bg-[var(--secondary)] text-white hover:bg-[var(--secondary-hover)] shadow-lg shadow-[var(--secondary)]/25 hover:shadow-xl hover:shadow-[var(--secondary)]/30 transform hover:scale-105":
              variant === "primary",
            // Secondary - Trust blue
            "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] shadow-lg shadow-[var(--primary)]/20":
              variant === "secondary",
            // Outline - Blue border
            "border-2 border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--primary)]/10":
              variant === "outline",
            "text-[var(--body)] hover:bg-gray-100": variant === "ghost",
          },
          {
            "px-4 py-2 text-sm": size === "sm",
            "px-6 py-3 text-base": size === "md",
            "px-8 py-4 text-lg": size === "lg",
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
