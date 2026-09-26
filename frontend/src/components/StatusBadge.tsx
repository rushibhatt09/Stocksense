/** One colour scheme for document status, used everywhere a status is shown. */

const STYLES: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  waiting: "bg-amber-100 text-amber-800",
  ready: "bg-blue-100 text-blue-800",
  done: "bg-emerald-100 text-emerald-800",
  canceled: "bg-rose-100 text-rose-800",
};

const LABELS: Record<string, string> = {
  draft: "Draft",
  waiting: "Waiting",
  ready: "Ready",
  done: "Done",
  canceled: "Canceled",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
        STYLES[status] ?? STYLES.draft
      }`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
