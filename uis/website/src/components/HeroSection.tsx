import Image from "next/image";
import Link from "next/link";

export function HeroSection() {
  return (
    <section
      className="mx-auto max-w-8xl px-6 mb-12 mt-8"
      aria-labelledby="hero-title"
    >
      <div className="overflow-hidden rounded-3xl border border-border bg-surface shadow-soft grid items-stretch md:grid-cols-12 gap-4">
        
        <div className="px-8 py-12 md:col-span-5 md:px-12 md:py-20 w-full flex flex-col justify-center">
          <p className="mb-4 text-sm uppercase tracking-[0.2em] text-foreground">
            Trusted Outpatient Healthcare
          </p>
          <h1
            id="hero-title"
            className="font-display text-4xl font-bold leading-tight text-foreground md:text-5xl"
          >
            Your health is our priority.
          </h1>
          <p className="mt-6 text-lg text-muted leading-relaxed text-left">
            Get safer care and faster access with HealthCore. We connect primary, specialist, and chronic care across 12 modern clinics to prioritize your health.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row text-base">
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

        <div className="pt-8 pb-8 pl-4 pr-6 md:col-span-7 flex items-center justify-center w-full min-h-[400px] md:min-h-[550px]">
          <div className="relative w-full h-full overflow-hidden rounded-2xl">
            <Image
              src="/images/doctorPatient.jpg"
              alt="HealthCore clinical team supporting a patient"
              fill
              priority
              quality={100}
              unoptimized
              className="object-cover object-[30%_center]"
            />
          </div>
        </div>

      </div>
    </section>
  );
}
