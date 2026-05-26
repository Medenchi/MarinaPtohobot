// Minimal brand footer used across all pages.

export default function Footer() {
  return (
    <footer className="footer-brand">
      <span>made with </span>
      <a
        href={import.meta.env.VITE_FOOTER_URL || "https://malinacode.is-a.dev"}
        target="_blank"
        rel="noreferrer"
      >
        malinacode.is-a.dev
      </a>
    </footer>
  );
}
