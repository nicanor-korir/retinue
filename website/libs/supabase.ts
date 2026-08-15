import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type WaitlistEntry = {
  id?: string
  email: string
  full_name: string
  company_name?: string
  use_case: string
  company_size?: string
  beta_tester: boolean
  updates: boolean
  created_at?: string
}
