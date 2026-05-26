export function shortId(prefix = "n"): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 8)}`;
}

export function classNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function readJsonFile<T = unknown>(file: File): Promise<T> {
  const text = await file.text();
  return JSON.parse(text);
}
