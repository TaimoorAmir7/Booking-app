"use client";

import { AuthForm } from "@/components/AuthForm";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { login } = useAuth();

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-teal-50 px-4">
      <AuthForm
        mode="login"
        onSubmit={async ({ email, password }) => login(email, password)}
      />
    </main>
  );
}
