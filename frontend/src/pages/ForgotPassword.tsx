import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Warehouse } from "lucide-react";

import { ApiError, api } from "../lib/api";

type Step = "email" | "otp" | "password";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleEmailSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data = await api<{ message: string; otp: string | null }>("/auth/forgot-password", {
        method: "POST",
        body: { email },
      });
      setDevOtp(data.otp);
      setStep("otp");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send the code");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleOtpSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data = await api<{ reset_token: string }>("/auth/verify-otp", {
        method: "POST",
        body: { email, otp },
      });
      setResetToken(data.reset_token);
      setStep("password");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "That code is invalid or has expired");
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setSubmitting(true);
    try {
      await api("/auth/reset-password", {
        method: "POST",
        body: { reset_token: resetToken, new_password: newPassword },
      });
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reset the password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 flex items-center gap-2">
          <Warehouse className="h-7 w-7 text-brand-500" />
          <span className="text-xl font-semibold text-slate-900">StockSense</span>
        </div>

        <h1 className="text-lg font-semibold text-slate-900">Reset your password</h1>
        <p className="mt-1 text-sm text-slate-500">
          {step === "email" && "Enter your account email to receive a 6-digit code."}
          {step === "otp" && "Enter the 6-digit code."}
          {step === "password" && "Choose a new password."}
        </p>

        <ol className="mt-4 flex gap-2 text-xs text-slate-400">
          <li className={step === "email" ? "font-semibold text-brand-600" : ""}>1. Email</li>
          <li>·</li>
          <li className={step === "otp" ? "font-semibold text-brand-600" : ""}>2. Code</li>
          <li>·</li>
          <li className={step === "password" ? "font-semibold text-brand-600" : ""}>3. New password</li>
        </ol>

        {step === "email" && (
          <form onSubmit={handleEmailSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label" htmlFor="fp-email">
                Email
              </label>
              <input
                id="fp-email"
                type="email"
                required
                className="input"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? "Sending…" : "Send code"}
            </button>
          </form>
        )}

        {step === "otp" && (
          <form onSubmit={handleOtpSubmit} className="mt-6 space-y-4">
            {devOtp && (
              <p className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-700">
                Dev mode — your code is <strong>{devOtp}</strong>
              </p>
            )}
            <div>
              <label className="label" htmlFor="fp-otp">
                6-digit code
              </label>
              <input
                id="fp-otp"
                required
                maxLength={6}
                className="input"
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
              />
            </div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? "Verifying…" : "Verify code"}
            </button>
          </form>
        )}

        {step === "password" && (
          <form onSubmit={handlePasswordSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label" htmlFor="fp-password">
                New password
              </label>
              <input
                id="fp-password"
                type="password"
                required
                className="input"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
              <p className="mt-1 text-xs text-slate-500">At least 8 characters.</p>
            </div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? "Saving…" : "Reset password"}
            </button>
          </form>
        )}

        <Link to="/login" className="mt-6 inline-block text-sm text-brand-600 hover:underline">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
