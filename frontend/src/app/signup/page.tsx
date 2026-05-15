"use client";

import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/lib/auth-context";

export default function SignupPage() {
  const { signup } = useAuth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-teal-50 px-4">
      <AuthForm
        mode="signup"
        onSubmit={async ({ email, password, fullName }) =>
          signup(email, password, fullName ?? "")
        }
      />
    </main>
  );
}
