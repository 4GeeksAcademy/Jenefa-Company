import Image from "next/image";
import Link from "next/link";

export function HeroSection() {
  return (
    <section
      className="mb-12 mt-8 overflow-hidden rounded-3xl border border-border bg-surface shadow-soft"
      aria-labelledby="hero-title"
    >
      <div className="grid items-stretch md:grid-cols-2">
        <div className="px-8 py-16 md:px-12 md:py-20">
          <p className="mb-4 text-xs uppercase tracking-[0.2em] text-foreground">
            Trusted Outpatient Healthcare
          </p>
          <h1
            id="hero-title"
            className="max-w-3xl font-display text-4xl font-bold leading-tight text-foreground md:text-5xl"
          >
            Your health is our priority.
          </h1>
          <p className="mt-6 max-w-3xl text-lg text-muted">
          Get safer care and faster access. HealthCore connects primary, specialist, and chronic care across 12 modern clinics to prioritize your health.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row">
            <Link
              href="/apply"
              className="inline-flex justify-center rounded-full bg-accent-500 px-6 py-3 font-semibold text-white hover:bg-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-500"
            >
              Start your application
            </Link>
            <a
              href="#contact"
              className="inline-flex justify-center rounded-full border border-blue-300 bg-surface px-6 py-3 font-semibold text-foreground hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              Speak with our team
            </a>
          </div>
        </div>
        <div className="hero-image-panel relative">
          <Image
            src="/images/doctorPatient.jpg"
            alt="HealthCore clinical team supporting a patient"
            fill
            priority
            className="object-cover object-center"
            sizes="(max-width: 768px) 100vw, 50vw"
          />
        </div>
      </div>
    </section>
  );
}
