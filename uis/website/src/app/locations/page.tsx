'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { MapPin, Phone, Clock, ArrowLeft } from 'lucide-react';

interface ClinicLocation {
  id: number;
  name: string;
  region: 'US' | 'UK';
  stateCity: string;
  address: string;
  phone: string;
  hours: string;
}

export default function LocationsPage() {
  const [activeLocation, setActiveLocation] = useState<ClinicLocation | null>(null);

  const clinics: ClinicLocation[] = [
    { id: 1, name: "Houston Medical Center Hub", region: "US", stateCity: "Texas, Houston", address: "6565 Fannin St, Houston, TX 77030", phone: "+1 (713) 555-0100", hours: "8:00 AM - 8:00 PM" },
    { id: 2, name: "Austin North Primary Care", region: "US", stateCity: "Texas, Austin", address: "1301 Barbara Jordan Blvd, Austin, TX 78723", phone: "+1 (512) 555-0122", hours: "8:00 AM - 7:00 PM" },
    { id: 3, name: "Dallas Downtown Health", region: "US", stateCity: "Texas, Dallas", address: "3500 Gaston Ave, Dallas, TX 75246", phone: "+1 (214) 555-0144", hours: "7:30 AM - 7:30 PM" },
    { id: 4, name: "Miami Brickell Specialist Centre", region: "US", stateCity: "Florida, Miami", address: "1100 Brickell Ave, Miami, FL 33131", phone: "+1 (305) 555-0155", hours: "8:00 AM - 6:00 PM" },
    { id: 5, name: "Orlando Community Clinic", region: "US", stateCity: "Florida, Orlando", address: "601 E Rollins St, Orlando, FL 32803", phone: "+1 (407) 555-0166", hours: "8:00 AM - 8:00 PM" },
    { id: 6, name: "Tampa Bay Chronic Care", region: "US", stateCity: "Florida, Tampa", address: "3000 Medical Park Dr, Tampa, FL 33613", phone: "+1 (813) 555-0177", hours: "8:30 AM - 5:30 PM" },
    { id: 7, name: "Atlanta Midtown Outpatient", region: "US", stateCity: "Georgia, Atlanta", address: "550 Peachtree St NE, Atlanta, GA 30308", phone: "+1 (404) 555-0188", hours: "8:00 AM - 7:00 PM" },
    { id: 8, name: "Savannah Health Hub", region: "US", stateCity: "Georgia, Savannah", address: "4700 Waters Ave, Savannah, GA 31404", phone: "+1 (912) 555-0199", hours: "8:00 AM - 6:00 PM" },
    { id: 9, name: "Alpharetta Family Wellness", region: "US", stateCity: "Georgia, Alpharetta", address: "3400 Old Milton Pkwy, Alpharetta, GA 30005", phone: "+1 (770) 555-0111", hours: "8:00 AM - 8:00 PM" },
    
    { id: 10, name: "London Harley Street Hub", region: "UK", stateCity: "London, City of Westminster", address: "84 Harley St, London W1G 7HW, UK", phone: "+44 20 7555 0143", hours: "08:00 - 20:00" },
    { id: 11, name: "London Canary Wharf Care", region: "UK", stateCity: "London, Tower Hamlets", address: "25 Canada Square, London E14 5LB, UK", phone: "+44 20 7555 0199", hours: "07:30 - 19:30" },
    { id: 12, name: "Manchester City Centre Clinic", region: "UK", stateCity: "Manchester, Piccadilly", address: "1 Piccadilly, Manchester M1 1RG, UK", phone: "+44 161 555 0122", hours: "08:00 - 18:30" }
  ];

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="mx-auto max-w-none flex flex-col lg:flex-row h-screen overflow-hidden">
        
        {/* LEFT COLUMN: List of Clinics */}
        <section className="w-full lg:w-[45%] h-full overflow-y-auto px-6 py-8 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700">
          <Link href="/" className="inline-flex items-center text-sm font-medium text-blue-600 hover:underline mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Homepage
          </Link>
          
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Our Global Network</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 mb-8">
            Hover over a clinic to locate its coordinates and view operational cross-border infrastructure instantly.
          </p>

          <div className="space-y-4">
            {clinics.map((clinic) => (
              <article
                key={clinic.id}
                onMouseEnter={() => setActiveLocation(clinic)}
                className={`p-5 rounded-2xl border transition-all duration-300 cursor-pointer ${
                  activeLocation?.id === clinic.id
                    ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20 shadow-sm'
                    : 'border-slate-100 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 mb-2">
                      {clinic.stateCity}
                    </span>
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white">{clinic.name}</h2>
                  </div>
                </div>

                <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                  <p className="flex items-center"><MapPin className="w-4 h-4 mr-2 text-slate-400 shrink-0" /> {clinic.address}</p>
                  <p className="flex items-center"><Phone className="w-4 h-4 mr-2 text-slate-400 shrink-0" /> {clinic.phone}</p>
                  <p className="flex items-center"><Clock className="w-4 h-4 mr-2 text-slate-400 shrink-0" /> {clinic.hours}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* REPLACED RIGHT COLUMN: Clean, Working Interactive Map Engine */}
               {/* RIGHT COLUMN: The Sticky Live Map Canvas */}
               <section className="w-full lg:w-[55%] h-[40vh] lg:h-full relative bg-slate-100 dark:bg-slate-950 flex flex-col justify-between">
          
          {/* Status Floating Box overlay */}
          {activeLocation ? (
            <div className="absolute top-6 left-6 right-6 z-10 bg-white/95 backdrop-blur-md p-4 rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800/95 shadow-xl max-w-sm transition-all duration-300">
              <p className="text-xs uppercase font-bold tracking-wider text-blue-600 dark:text-blue-400 mb-1">Target Facility Selected</p>
              <h3 className="font-bold text-slate-900 dark:text-white">{activeLocation.name}</h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">{activeLocation.address}</p>
            </div>
          ) : (
            <div className="absolute top-6 left-6 right-6 z-10 bg-slate-900/90 backdrop-blur-md p-4 rounded-xl text-white max-w-xs text-center text-xs shadow-md">
              💡 Hover over any clinic card on the left to load its live interactive satellite navigation routing.
            </div>
          )}
          
          {/* Dynamic Map Framework Wrapper */}
          <div className="w-full h-full relative">
            {activeLocation ? (
              <iframe
                key={activeLocation.id} // Forces the iframe to immediately reload new location data on hover
                title={`Map location for ${activeLocation.name}`}
                width="100%"
                height="100%"
                style={{ border: 0 }}
                loading="lazy"
                src={`https://google.com{encodeURIComponent(activeLocation.address)}&t=&z=14&ie=UTF8&iwloc=&output=embed`}
  className="w-full h-full min-h-[40vh] lg:h-full"
/>
            ) : (
              /* Global fallback overview map before user starts hovering */
              <iframe
                title="HealthCore Global Operations Overview Map"
                width="100%"
                height="100%"
                style={{ border: 0 }}
                loading="lazy"
                src="https://google.com"
                className="w-full h-full opacity-80"
              />
            )}
          </div>
        </section>


      </div>
    </main>
  );
}