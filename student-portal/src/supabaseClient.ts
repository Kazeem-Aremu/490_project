import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// The browser must use the PUBLISHABLE key (sb_publishable_…). VITE_SUPABASE_ANON_KEY is accepted for older
// projects that call it the anon key. Never put the secret key in any VITE_ variable.
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? import.meta.env.VITE_SUPABASE_ANON_KEY

let client: SupabaseClient | null = null
try {
  // Secret/service keys bypass all security and must only live on the Python server (Server/.env)
  if (String(supabaseKey).startsWith("sb_secret_")) {
    throw new Error("A Supabase SECRET key is set for the browser. Put the publishable key (sb_publishable_…) in VITE_SUPABASE_PUBLISHABLE_KEY in .env.local instead.")
  }
  client = createClient(supabaseUrl, supabaseKey)
} catch (e) {
  console.error("Supabase: check VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY in .env.local", e)
}

export const supabase = client
