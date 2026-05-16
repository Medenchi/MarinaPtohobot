import { SpinnerGap } from "@phosphor-icons/react";

export default function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20">
      <SpinnerGap size={32} className="animate-spin text-muted" />
      {label && <p className="text-sm text-muted">{label}</p>}
    </div>
  );
}
