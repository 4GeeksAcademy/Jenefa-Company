export const siteConfig = {
  name: "HealthCore",
  tagline: "Modern Outpatient Care",
  description:
    "HealthCore provides same-day outpatient healthcare across the US and UK with primary care, specialist consultations, and chronic care management.",
  phone: "+1-800-442-5844",
  email: "access@healthcore.com",
  url: "https://healthcore.example.com",
} as const;

export type ServiceCard = {
  
  title: string;
  image: string;
  href: string;
};

export const services: ServiceCard[] = [
  {
    
    title: "Primary Care",
    description: "Preventive visits, diagnosis, and ongoing support for all ages.",
    image: "/images/doctorHeart.jpg",
    href: "/apply",
  },
  {
    
    title: "Specialist Consultations",
    description: "Fast access to specialist reviews without long waiting times.",
    image: "/images/kidsTeddy.jpg",
    href: "/apply",
  },
  {
    
    title: "Chronic Disease Management",
    description: "Long-term plans for diabetes, heart health, and ongoing conditions.",
    image: "/images/hospitalEmployee.jpg",
    href: "/apply",
  },
  {
    
    title: "Preventive Programmes",
    description: "Screenings and wellness pathways focused on early intervention.",
    image: "/images/yogaWellness.jpg",
    href: "/apply",
  },
];

export type BenefitCard = {
  eyebrow: string;
  title: string;
  
  image: string;
  href: string;
  tall?: boolean;
};

export const benefits: BenefitCard[] = [
  {
    eyebrow: "Our Locations",
    title: "12 Clinics - One Standard",
    description: "Consistent care quality across every location in two countries.",
    image: "/images/ourLocations.jpg",
    href: "/locations",
  },
  {
    eyebrow: "Same Day",
    title: "Faster Access",
    description: "Same-day bookings and extended hours when you need care quickly.",
    image: "/images/fastAccess.jpg",
    href: "/apply",
  },
  {
    eyebrow: "Bilingual",
    title: "Inclusive Experience",
    description: "Bilingual staff in US and UK supporting clear, accessible care.",
    image: "/images/customerSupport.jpg",
    href: "/#contact",
  },
];

export type ContactOffice = {
  title: string;
  address: string;
  phone: string;
  email: string;
  hours: string;
};

export const contactOffices: ContactOffice[] = [
  {
    title: "HealthCore Patient Access",
    address: "1201 Medical Park Drive, Austin, TX, USA 98321",
    phone: "+1 (800) 442-5844",
    email: "access@healthcore.com",
    hours: "Mon-Sat, 6:00-22:00",
  },
  {
    title: "HealthCore Patient Access",
    address: "135-155 Yorkson St, London, UK SE1 8UG",
    phone: "+44 (2079) 460958",
    email: "access@healthcore.com",
    hours: "Mon-Sat, 7:00-20:00",
  },
];

export const clinicLocationsByCountry = {
  US: ["Austin", "Houston", "Miami", "Atlanta"],
  UK: ["London", "Manchester"],
} as const;

export type CountryCode = keyof typeof clinicLocationsByCountry;

export const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Hospital",
  name: siteConfig.name,
  description:
    "Outpatient healthcare services with 12 clinics across the United States and the United Kingdom.",
  url: siteConfig.url,
  telephone: siteConfig.phone,
  address: {
    "@type": "PostalAddress",
    addressLocality: "Austin",
    addressRegion: "Texas",
    addressCountry: "US",
  },
  areaServed: ["United States", "United Kingdom"],
  medicalSpecialty: [
    "PrimaryCare",
    "ChronicCare",
    "PreventiveMedicine",
    "InternalMedicine",
  ],
};
