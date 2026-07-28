import type { Metadata } from "next";
import { ApplicationForm } from "@/components/ApplicationForm";
import { SiteHeader } from "@/components/SiteHeader";
import { SkipLink } from "@/components/SkipLink";

export const metadata: Metadata = {
  title: "HealthCore Application | Start Your Care Journey",
  description:
    "Apply to HealthCore and request your outpatient consultation with complete personal and medical intake details.",
};

export default function ApplyPage() {
  return (
    <>
      <SkipLink />
      <SiteHeader variant="apply" />
      <main id="main-content" className="mx-auto max-w-4xl px-6 py-12">
        <section aria-labelledby="form-title" className="mb-8">
          <h1 id="form-title" className="font-display text-3xl font-bold text-foreground md:text-4xl">
            Patient Application Form
          </h1>
          <p className="mt-3 text-muted">
            Complete all fields so our patient access team can safely schedule your first
            consultation.
          </p>
        </section>
        <ApplicationForm />
      </main>
    </>
  );
}
