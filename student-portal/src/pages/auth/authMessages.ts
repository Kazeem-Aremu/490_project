// Shared bits for the auth pages (Login, Signup, ForgotPassword, ResetPassword)

export const NOT_CONFIGURED =
  "Sign in isn't set up yet: add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to .env.local.";

// Supabase's built-in email service only sends a few emails per hour per project
export function authError(e: unknown) {
  const text = e instanceof Error ? e.message : String(e);
  if (/rate limit/i.test(text)) {
    return "Too many emails were sent recently (Supabase's built-in email allows only a few per hour). " +
      "Try again later, or ask the team to create your account with Server/createTestUser.py.";
  }
  return text;
}
