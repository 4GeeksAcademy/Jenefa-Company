import Link from "next/link";

type SiteHeaderProps = {
  variant?: "home" | "apply";
};

export function SiteHeader({ variant = "home" }: SiteHeaderProps) {
  return (
    <header className="border-b border-border bg-surface">
      <div className={`mx-auto px-6 ${variant === "home" ? "max-w-7xl py-6" : "max-w-4xl py-4"}`}>
        <nav className="flex items-center justify-between" aria-label="Main navigation">
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex h-10 w-10 items-center justify-center rounded-xl font-bold text-white ${
                variant === "apply" ? "bg-accent-500" : "bg-accent-600"
              }`}
            >
              HC
            </span>
            <Link
              href="/"
              className="font-semibold text-2xl tracking-wide text-foreground hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-brand-600 rounded"
            >
              HealthCore
            </Link>
          </div>

          {variant === "home" ? (
            <ul className="flex items-center gap-6 text-sm text-foreground md:text-base">
              <li>
                <a
                  href="#services"
                  className="hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-brand-600 rounded"
                >
                  Services
                </a>
              </li>
              <li>
                <a
                  href="#benefits"
                  className="hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-brand-600 rounded"
                >
                  Why Us
                </a>
              </li>
              <li>
                <a
                  href="#contact"
                  className="hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-brand-600 rounded"
                >
                  Contact
                </a>
              </li>
              <li>
                <Link
                  href="/apply"
                  className="inline-flex items-center rounded-full bg-accent-500 px-4 py-2 font-medium text-white hover:bg-accent-600 focus:outline-none focus:ring-2 focus:ring-brand-600"
                >
                  Apply Now
                </Link>
              </li>
            </ul>
          ) : (
            <Link
              href="/"
              className="text-sm text-foreground hover:text-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-600 rounded"
            >
              Back to homepage
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
