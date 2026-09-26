import PageHeader from "../components/PageHeader";
import { useAuth } from "../auth/AuthContext";

const ROLE_LABELS: Record<string, string> = {
  manager: "Inventory Manager",
  staff: "Warehouse Staff",
};

export default function Profile() {
  const { user, signOut } = useAuth();

  return (
    <>
      <PageHeader title="My Profile" subtitle="Your account details." />

      <div className="card max-w-lg divide-y divide-slate-200">
        <dl className="p-5">
          <div className="flex justify-between py-2">
            <dt className="text-sm text-slate-500">Name</dt>
            <dd className="text-sm font-medium text-slate-800">{user?.name ?? "—"}</dd>
          </div>
          <div className="flex justify-between py-2">
            <dt className="text-sm text-slate-500">Email</dt>
            <dd className="text-sm font-medium text-slate-800">{user?.email ?? "—"}</dd>
          </div>
          <div className="flex justify-between py-2">
            <dt className="text-sm text-slate-500">Role</dt>
            <dd className="text-sm font-medium text-slate-800">
              {user ? (ROLE_LABELS[user.role] ?? user.role) : "—"}
            </dd>
          </div>
        </dl>
        <div className="p-5">
          <button type="button" className="btn-secondary" onClick={signOut}>
            Logout
          </button>
        </div>
      </div>
    </>
  );
}
