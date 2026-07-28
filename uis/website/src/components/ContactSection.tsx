import Link from "next/link";
import { contactOffices } from "@/lib/site";

export function ContactSection() {
  return (
    <section id="contact" className="mx-auto max-w-6xl px-6 py-16" aria-labelledby="contact-title">
      <div className="grid items-start gap-8 md:grid-cols-2">
        <div>
          <h2 id="contact-title" className="font-display text-3xl font-bold text-foreground">
            Take your first step with us
          </h2>
          <p className="mt-4 text-foreground">
            Submit your healthcare application and our access team
          </p>
          <p className="mt-2 text-foreground">will follow up to schedule your first visit.</p>
          <Link
            href="/apply"
            className="mt-6 inline-flex rounded-full bg-accent-500 px-6 py-3 font-semibold text-white hover:bg-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-100"
          >
            Go to application form
          </Link>
        </div>

        <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-2">
          {contactOffices.map((office) => (
            <address
              key={office.address}
              className="rounded-2xl border border-border bg-surface p-6 text-muted not-italic shadow-sm"
            >
              <p className="font-semibold text-foreground">{office.title}</p>
              <p className="mt-2">{office.address}</p>
              <p className="mt-1">Phone: {office.phone}</p>
              <p className="mt-1">Email: {office.email}</p>
              <p className="mt-1">Hours: {office.hours}</p>
            </address>
          ))}
        </div>
      </div>
    </section>
  );
}
