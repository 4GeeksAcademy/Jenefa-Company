import { benefits } from "@/lib/site";
import { ImageLinkCard } from "@/components/ImageLinkCard";

export function BenefitsSection() {
  return (
    <section id="benefits" className="border-y border-border bg-sky-50">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="font-display text-4xl font-bold text-foreground">
          Why patients choose HealthCore
        </h2>
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {benefits.map((benefit) => (
            <ImageLinkCard
              key={benefit.title}
              href={benefit.href}
              image={benefit.image}
              title={benefit.title}
              eyebrow={benefit.eyebrow}
              tall={benefit.tall}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
