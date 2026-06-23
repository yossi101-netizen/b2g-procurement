import type { Metadata } from "next";
import BlogClient from "./BlogClient";
import { blogArticles } from "@/data/blogs";



export const metadata: Metadata = {
  title: "Blog — Leather Manufacturing Knowledge | KRITIKAAL",
  description:
    "Expert articles on leather manufacturing in India — AQL quality control, EUDR compliance, MOQ, lead times, tannery clusters, and supply chain. Written by KRITIKAAL for global brand buyers.",
  alternates: {
    canonical: "https://www.kritikaal.com/blog",
  },
  openGraph: {
    title: "Blog — Leather Manufacturing Knowledge | KRITIKAAL",
    description:
      "Expert articles on leather manufacturing in India — AQL, EUDR, MOQ, lead times, and supply chain. KRITIKAAL is India's managed leather manufacturing partner.",
    url: "https://www.kritikaal.com/blog",
    siteName: "KRITIKAAL",
    locale: "en_IN",
    type: "website",
    images: ["/KRITIKAAL Logo.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Blog — Leather Manufacturing Knowledge | KRITIKAAL",
    description:
      "Expert articles on leather manufacturing from India — AQL, EUDR compliance, MOQ, lead times, and supply chain.",
    images: ["/KRITIKAAL Logo.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
};

// Blog list JSON-LD — ItemList for AI crawlers
const blogListJsonLd = {
  "@context": "https://schema.org",
  "@type": "ItemList",
  name: "KRITIKAAL Leather Manufacturing Blog",
  description:
    "Expert articles on leather manufacturing in India for global brand buyers.",
  url: "https://www.kritikaal.com/blog",
  numberOfItems: blogArticles.length,
  itemListElement: blogArticles.map((article, i) => ({
    "@type": "ListItem",
    position: i + 1,
    url: `https://www.kritikaal.com/blog/${article.slug}`,
    name: article.title,
  })),
};

export default function BlogPage() {
  return (
    <>
      {/* JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(blogListJsonLd) }}
      />
      <BlogClient />
    </>
  );
}
