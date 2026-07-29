import { services } from "@/lib/site";
import { ImageLinkCard } from "@/components/ImageLinkCard";

export function ServicesSection() {
  return (
    <section id="services" className="mx-auto max-w-7xl px-6 py-16" aria-labelledby="services-title">
      <h2 id="services-title" className="font-display text-4xl font-bold text-foreground">
        Core Services
      </h2>
      <p className="mt-3 max-w-3xl text-muted">
      Connecting primary, specialist, and continuous care within a single seamless system. Designed to cut out administrative wait times and prioritize your long-term health.
      </p>
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {services.map((service) => (
          <ImageLinkCard
            key={service.title}
            href={service.href}
            image={service.image}
            title={service.title}
          />
        ))}
      </div>
    </section>
  );
}
