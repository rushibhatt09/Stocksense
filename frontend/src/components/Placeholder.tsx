/** Temporary body for a page whose real content lands in a later hour. */

export default function Placeholder({ note }: { note: string }) {
  return (
    <div className="card p-8 text-center">
      <p className="text-sm text-slate-500">{note}</p>
    </div>
  );
}
