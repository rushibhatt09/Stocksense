import { Link } from "react-router-dom";
import { Warehouse } from "lucide-react";

/**
 * Three steps: email -> 6-digit OTP -> new password.
 * The steps are wired to /auth/forgot-password, /auth/verify-otp and
 * /auth/reset-password in the next commit.
 */
export default function ForgotPassword() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 flex items-center gap-2">
          <Warehouse className="h-7 w-7 text-brand-500" />
          <span className="text-xl font-semibold text-slate-900">StockSense</span>
        </div>

        <h1 className="text-lg font-semibold text-slate-900">Reset your password</h1>
        <p className="mt-1 text-sm text-slate-500">
          We will email you a 6-digit code to confirm it is you.
        </p>

        <ol className="mt-6 space-y-3 text-sm text-slate-600">
          <li className="rounded-lg border border-slate-200 px-3 py-2">1. Enter your email</li>
          <li className="rounded-lg border border-slate-200 px-3 py-2">2. Enter the 6-digit code</li>
          <li className="rounded-lg border border-slate-200 px-3 py-2">3. Choose a new password</li>
        </ol>

        <Link to="/login" className="mt-6 inline-block text-sm text-brand-600 hover:underline">
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
