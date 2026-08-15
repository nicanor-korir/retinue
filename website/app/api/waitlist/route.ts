import { NextRequest, NextResponse } from "next/server"
import { z } from "zod"
import { supabase } from "@/libs/supabase"

const waitlistSchema = z.object({
  email: z.string().email("Invalid email address"),
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  companyName: z.string().optional(),
  useCase: z.string().min(1, "Use case is required"),
  companySize: z.string().optional(),
  betaTester: z.boolean().default(false),
  updates: z.boolean().default(true),
})

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate the data
    const validatedData = waitlistSchema.parse(body)

    // Insert into Supabase
    const { data, error } = await supabase
      .from('waitlist')
      .insert([
        {
          email: validatedData.email,
          full_name: validatedData.fullName,
          company_name: validatedData.companyName || null,
          use_case: validatedData.useCase,
          company_size: validatedData.companySize || null,
          beta_tester: validatedData.betaTester,
          updates: validatedData.updates,
        },
      ])
      .select()

    if (error) {
      console.error('Supabase error:', error)

      // Check for duplicate email
      if (error.code === '23505') {
        return NextResponse.json(
          {
            success: false,
            message: "This email is already on the waitlist",
          },
          { status: 409 }
        )
      }

      return NextResponse.json(
        {
          success: false,
          message: "Failed to submit to waitlist",
        },
        { status: 500 }
      )
    }

    return NextResponse.json(
      {
        success: true,
        message: "Successfully joined the waitlist",
        data,
      },
      { status: 201 }
    )
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          success: false,
          message: "Validation error",
          errors: error.issues,
        },
        { status: 400 }
      )
    }

    console.error("Error processing waitlist submission:", error)
    return NextResponse.json(
      {
        success: false,
        message: "Internal server error",
      },
      { status: 500 }
    )
  }
}
