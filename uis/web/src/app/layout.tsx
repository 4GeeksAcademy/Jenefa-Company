import type { Metadata } from "next";
import { Fraunces, Manrope } from "next/font/google";
import { WebShell } from "@/components/WebShell";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HealthCore Web",
  description:
    "Internal operations workspace for HealthCore Digital — clinical, billing, and compliance tools.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${manrope.variable} ${fraunces.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <WebShell>{children}</WebShell>
      </body>
    </html>
  );
}
