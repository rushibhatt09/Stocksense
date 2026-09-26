import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3">
      <p className="text-3xl font-semibold text-slate-900">404</p>
      <p className="text-sm text-slate-500">That page does not exist.</p>
      <Link to="/dashboard" className="btn-primary mt-2">
        Back to dashboard
      </Link>
    </div>
  );
}
