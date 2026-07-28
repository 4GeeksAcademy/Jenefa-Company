import { services } from "@/lib/site";
import { ImageLinkCard } from "@/components/ImageLinkCard";

export function ServicesSection() {
  return (
    <section id="services" className="mx-auto max-w-6xl px-6 py-16" aria-labelledby="services-title">
      <h2 id="services-title" className="font-display text-6xl font-bold text-foreground">
        Core Services
      </h2>
      <p className="mt-3 max-w-3xl text-muted">
        Designed for modern outpatient care delivery with continuity across locations.
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
