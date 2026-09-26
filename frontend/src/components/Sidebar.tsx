import { NavLink } from "react-router-dom";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Package,
  Repeat,
  Scale,
  Settings,
  User,
  Warehouse,
} from "lucide-react";

import { useAuth } from "../auth/AuthContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
    isActive ? "bg-brand-500 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white",
  ].join(" ");

export default function Sidebar() {
  const { user, signOut } = useAuth();

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-slate-900 p-4">
      <div className="mb-6 flex items-center gap-2 px-2">
        <Warehouse className="h-6 w-6 text-brand-500" />
        <span className="text-lg font-semibold text-white">StockSense</span>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto">
        <NavLink to="/dashboard" className={linkClass}>
          <LayoutDashboard className="h-4 w-4" /> Dashboard
        </NavLink>
        <NavLink to="/products" className={linkClass}>
          <Package className="h-4 w-4" /> Products
        </NavLink>

        <p className="px-3 pb-1 pt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Operations
        </p>
        <NavLink to="/receipts" className={linkClass}>
          <ArrowDownToLine className="h-4 w-4" /> Receipts
        </NavLink>
        <NavLink to="/deliveries" className={linkClass}>
          <ArrowUpFromLine className="h-4 w-4" /> Delivery Orders
        </NavLink>
        <NavLink to="/transfers" className={linkClass}>
          <Repeat className="h-4 w-4" /> Internal Transfers
        </NavLink>
        <NavLink to="/adjustments" className={linkClass}>
          <Scale className="h-4 w-4" /> Inventory Adjustment
        </NavLink>
        <NavLink to="/moves" className={linkClass}>
          <ClipboardList className="h-4 w-4" /> Move History
        </NavLink>

        <p className="px-3 pb-1 pt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Settings
        </p>
        <NavLink to="/settings/warehouses" className={linkClass}>
          <Settings className="h-4 w-4" /> Warehouses
        </NavLink>
      </nav>

      <div className="mt-4 border-t border-slate-800 pt-4">
        <NavLink to="/profile" className={linkClass}>
          <User className="h-4 w-4" />
          <span className="truncate">{user?.name ?? "My Profile"}</span>
        </NavLink>
        <button
          type="button"
          onClick={signOut}
          className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white"
        >
          <LogOut className="h-4 w-4" /> Logout
        </button>
      </div>
    </aside>
  );
}
