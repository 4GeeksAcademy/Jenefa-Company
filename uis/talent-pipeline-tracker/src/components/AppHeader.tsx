import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b border-teal-800 bg-teal-900 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-teal-200">
            HealthCore Digital · People & Workforce
          </p>
          <h1 className="text-xl font-bold">Candidate Sourcing Workspace</h1>
          <p className="mt-1 text-sm text-teal-100">
            Internal tool for recruitment team of Diane Foster
          </p>
        </div>
        <nav className="flex flex-wrap gap-2">
          <Link
            href="/"
            className="rounded-md bg-teal-700 px-4 py-2 text-sm font-medium hover:bg-teal-600"
          >
            Candidate Roster
          </Link>
          <Link
            href="/candidates/new"
            className="rounded-md border border-teal-400 px-4 py-2 text-sm font-medium hover:bg-teal-800"
          >
            Register Applicant
          </Link>
        </nav>
      </div>
    </header>
  );
}
