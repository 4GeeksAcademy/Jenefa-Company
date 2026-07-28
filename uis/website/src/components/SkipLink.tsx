export function SkipLink() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 rounded bg-surface px-4 py-2 text-foreground"
    >
      Skip to main content
    </a>
  );
}
