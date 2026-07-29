import { BenefitsSection } from "@/components/BenefitsSection";
import { ContactSection } from "@/components/ContactSection";
import { HeroSection } from "@/components/HeroSection";
import { ServicesSection } from "@/components/ServicesSection";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { SkipLink } from "@/components/SkipLink";

export default function HomePage() {
  return (
    <>
      <SkipLink />
      <SiteHeader variant="home" />
      <div className="mx-auto max-w-8xl px-6">
        <HeroSection />
      </div>
      <main id="main-content">
        <ServicesSection />
        <BenefitsSection />
        <ContactSection />
      </main>
      <SiteFooter />
    </>
  );
}
