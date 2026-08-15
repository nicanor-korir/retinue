import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import { Navbar } from "@/components/ui/navbar";
import { Footer } from "@/components/sections/Footer";

export const metadata: Metadata = {
  title: "Retinue - Build Business Solutions with a reliable team as Fast as You Can Describe It",
  description:
    "Autonomous AI agents team that develop software automatically. From idea to deployed product in hours, not months. Minutes, not weeks. Hundreds, not thousands. Retinue built our stack differently.",
  keywords: [
    "AI software development",
    "autonomous AI agents",
    "automated development",
    "AI developers",
    "software automation",
    "Retinue AI",
    "custom software hours",
    "AI agents build software",
    "autonomous development",
    "rapid software development",
  ],
  authors: [{ name: "Retinue" }],
  creator: "Retinue",
  publisher: "Retinue",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://retinue.team/",
    title: "Retinue - Build Software as Fast as You Can Describe It",
    description:
      "Autonomous AI agents that develop software automatically. Hours, not months. Hundreds, not thousands.",
    siteName: "Retinue",
    images: [
      {
        url: "/about.png",
        width: 1200,
        height: 630,
        alt: "Retinue - Autonomous AI Software Development",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Retinue - Build Software as Fast as You Can Describe It",
    description:
      "Autonomous AI agents that develop software automatically. Hours, not months. Hundreds, not thousands.",
    images: ["/about.png"],
    creator: "@retinueteam",
  },
  icons: {
    icon: [
      { url: '/favicon.png', sizes: 'any', type: 'image/png' },
    ],
    apple: [
      { url: '/favicon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      { rel: 'mask-icon', url: '/favicon.png', color: '#FF6B35' },
    ],
  },
};

// Next.js 14+ requires viewport and themeColor in their own `viewport` export
// rather than in `metadata`. Keeping them in metadata warns on every route and
// is removed in a future major version.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0066FF",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Google Analytics - Replace GA_MEASUREMENT_ID with your actual tracking ID */}
        <Script
          strategy="afterInteractive"
          src="https://www.googletagmanager.com/gtag/js?id=G-K74BV8831Q"
        />
        <Script
          id="google-analytics"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', 'G-K74BV8831Q');
            `,
          }}
        />

        {/* Structured Data - Organization */}
        <Script
          id="structured-data-org"
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              name: "Retinue",
              url: "https://retinue.team",
              logo: "https://retinue.team/favicon.png",
              description: "Autonomous AI agents that develop software automatically. Build software as fast as you can describe it.",
              foundingDate: "2025-10-01",
              founders: [
                {
                  "@type": "Person",
                  name: "Nicanor Korir",
                  jobTitle: "Founder & CEO",
                },
              ],
              address: {
                "@type": "PostalAddress",
                addressLocality: "Nairobi",
                addressCountry: "KE",
              },
              sameAs: [
                "https://twitter.com/nicanor-korir",
                "https://linkedin.com/company/nicanor-korir",
              ],
              contactPoint: {
                "@type": "ContactPoint",
                email: "hello@retinue.team",
                contactType: "Customer Service",
              },
            }),
          }}
        />

        {/* Structured Data - SoftwareApplication */}
        <Script
          id="structured-data-app"
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "Retinue",
              applicationCategory: "DeveloperApplication",
              offers: {
                "@type": "Offer",
                price: "99",
                priceCurrency: "USD",
              },
              aggregateRating: {
                "@type": "AggregateRating",
                ratingValue: "4.9",
                ratingCount: "500",
              },
              operatingSystem: "Web",
              description: "Autonomous AI agents that develop software automatically. 7 specialized AI agents function as CEO, CTO, engineers, and designers to deliver production-ready software in hours.",
            }),
          }}
        />

        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
