import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { classNames } from "@/lib/util";

interface BaseProps {
  label: string;
  hint?: string;
  error?: string;
}

type InputProps = BaseProps & InputHTMLAttributes<HTMLInputElement>;
type TextareaProps = BaseProps & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextField({ label, hint, error, className, ...rest }: InputProps) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <input
        {...rest}
        className={classNames(
          "w-full border border-line rounded-md px-3 py-2 text-sm bg-white",
          "focus:outline-none focus:border-ink",
          error && "border-red-500",
          className,
        )}
      />
      {hint && <span className="block text-xs text-muted mt-1">{hint}</span>}
      {error && <span className="block text-xs text-red-600 mt-1">{error}</span>}
    </label>
  );
}

export function TextArea({ label, hint, error, className, rows = 3, ...rest }: TextareaProps) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <textarea
        {...rest}
        rows={rows}
        className={classNames(
          "w-full border border-line rounded-md px-3 py-2 text-sm bg-white",
          "focus:outline-none focus:border-ink resize-y",
          error && "border-red-500",
          className,
        )}
      />
      {hint && <span className="block text-xs text-muted mt-1">{hint}</span>}
      {error && <span className="block text-xs text-red-600 mt-1">{error}</span>}
    </label>
  );
}

export function Switch({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer select-none">
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={classNames(
          "mt-0.5 relative inline-flex h-5 w-9 shrink-0 rounded-full border border-line transition-colors",
          checked ? "bg-ink" : "bg-white",
        )}
      >
        <span
          className={classNames(
            "inline-block h-4 w-4 rounded-full bg-paper shadow transition-transform",
            checked ? "translate-x-4" : "translate-x-0.5",
          )}
        />
      </button>
      <span>
        <span className="block text-sm text-ink">{label}</span>
        {hint && <span className="block text-xs text-muted">{hint}</span>}
      </span>
    </label>
  );
}
