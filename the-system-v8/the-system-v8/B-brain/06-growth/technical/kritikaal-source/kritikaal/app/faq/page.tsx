import type { Metadata } from "next";
import FAQClient from "./FAQClient";
import { faqData } from "@/data/faqData";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "FAQ — Leather Manufacturing from India | KRITIKAAL",
  description:
    "29 answers to the most-asked questions about leather manufacturing in India — MOQ, REACH/CA65 compliance, AQL 2.5 QC, lead times, Agra/Kanpur/Kolkata clusters, OEM, private label, and more. KRITIKAAL is India's managed leather manufacturing partner.",
  alternates: {
    canonical: "https://www.kritikaal.com/faq",
  },
  openGraph: {
    title: "FAQ — Leather Manufacturing from India | KRITIKAAL",
    description:
      "29 answers to the most-asked questions about sourcing leather goods from India. KRITIKAAL — India's managed leather manufacturing partner for UK, EU, USA, Australia, and Israel brands.",
    url: "https://www.kritikaal.com/faq",
    siteName: "KRITIKAAL",
    locale: "en_IN",
    type: "website",
    images: ["/KRITIKAAL Logo.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "FAQ — Leather Manufacturing from India | KRITIKAAL",
    description:
      "29 answers about leather manufacturing in India — MOQ, compliance, QC, lead times, clusters, OEM, and more.",
    images: ["/KRITIKAAL Logo.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};

// FAQPage JSON-LD structured data — schema.org/FAQPage
// Enables Google AI Overviews, rich results, and AI citation markup
const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqData.map((item) => ({
    "@type": "Question",
    name: item.question,
    acceptedAnswer: {
      "@type": "Answer",
      text: item.answer,
    },
  })),
};

export default function FAQPage() {
  return (
    <>
      {/* FAQPage JSON-LD — crawlable by Google, GPTBot, ClaudeBot, PerplexityBot */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <FAQClient />
    </>
  );
}
