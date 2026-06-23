import type { Metadata } from "next";
import { ClientProviders } from "@/components/ClientProviders";
import "@/index.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.kritikaal.com"),
  title: {
    default: 'KRITIKAAL | Managed Leather Manufacturing from India',
    template: '%s | KRITIKAAL',
  },
  description: "KRITIKAAL is India's managed leather manufacturing partner — sample development, factory selection (Agra, Kanpur, Kolkata), AQL quality control, REACH/CA65 compliance, and export logistics.",
  authors: [{ name: "KRITIKAAL" }],
  openGraph: {
    title: 'KRITIKAAL | Managed Leather Manufacturing from India',
    siteName: 'KRITIKAAL',
    locale: 'en_IN',
    type: 'website',
    images: ["/KRITIKAAL Logo.png"],
  },
  twitter: {
    card: "summary_large_image",
    site: "@KRITIKAAL",
    images: ["/KRITIKAAL Logo.png"],
  },
  icons: {
    icon: "/KRITIKAAL Logo.png",
    apple: "/KRITIKAAL Logo.png",
    shortcut: "/KRITIKAAL Logo.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Allura&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}

