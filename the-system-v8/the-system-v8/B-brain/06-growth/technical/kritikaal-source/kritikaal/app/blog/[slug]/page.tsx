import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  getBlogBySlug,
  getRelatedArticles,
  allBlogSlugs,
  type BlogArticle,
  type BlogSection,
} from "@/data/blogs";
import { ArrowRight, Calendar, Clock, User, ChevronRight, BookOpen } from "lucide-react";

// Static export — pre-render all blog pages at build time
export function generateStaticParams() {
  return allBlogSlugs.map((slug) => ({ slug }));
}

// Dynamic per-article SEO metadata
export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const article = getBlogBySlug(params.slug);
  if (!article) return {};

  return {
    title: `${article.title} | KRITIKAAL`,
    description: article.description,
    keywords: article.keywords,
    authors: [{ name: article.author }],
    alternates: {
      canonical: `https://www.kritikaal.com/blog/${article.slug}`,
    },
    openGraph: {
      title: article.title,
      description: article.description,
      url: `https://www.kritikaal.com/blog/${article.slug}`,
      siteName: "KRITIKAAL",
      locale: "en_IN",
      type: "article",
      publishedTime: article.publishedDate,
      modifiedTime: article.updatedDate ?? article.publishedDate,
      authors: [article.author],
      tags: article.tags,
      images: [article.image],
    },
    twitter: {
      card: "summary_large_image",
      title: article.title,
      description: article.description,
      images: [article.image],
    },
    robots: {
      index: true,
      follow: true,
      googleBot: { index: true, follow: true },
    },
  };
}

// ── JSON-LD helpers ─────────────────────────────────────────────────────────

function buildArticleJsonLd(article: BlogArticle) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    author: {
      "@type": "Person",
      name: article.author,
      jobTitle: article.authorTitle,
    },
    publisher: {
      "@type": "Organization",
      name: "KRITIKAAL",
      url: "https://www.kritikaal.com",
      logo: {
        "@type": "ImageObject",
        url: "https://www.kritikaal.com/KRITIKAAL Logo.png",
      },
    },
    datePublished: article.publishedDate,
    dateModified: article.updatedDate ?? article.publishedDate,
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": `https://www.kritikaal.com/blog/${article.slug}`,
    },
    image: `https://www.kritikaal.com${article.image}`,
    keywords: article.keywords.join(", "),
    articleSection: article.category,
  };
}

function buildBreadcrumbJsonLd(article: BlogArticle) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://www.kritikaal.com" },
      { "@type": "ListItem", position: 2, name: "Blog", item: "https://www.kritikaal.com/blog" },
      {
        "@type": "ListItem",
        position: 3,
        name: article.title,
        item: `https://www.kritikaal.com/blog/${article.slug}`,
      },
    ],
  };
}

function buildFaqJsonLd(article: BlogArticle) {
  if (!article.faqs?.length) return null;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: article.faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: { "@type": "Answer", text: faq.answer },
    })),
  };
}

import BlogDetailClient from "./BlogDetailClient";

// ── Page component ───────────────────────────────────────────────────────────

export default function BlogArticlePage({ params }: { params: { slug: string } }) {
  const article = getBlogBySlug(params.slug);
  if (!article) notFound();

  const related = getRelatedArticles(article.slug);
  const faqJsonLd = buildFaqJsonLd(article);

  // Build ToC entries
  const tocEntries = article.sections
    .filter((s) => s.heading)
    .flatMap((s) => [
      { id: s.id, label: s.heading, isTop: true },
      ...(s.subsections?.map((sub) => ({ id: sub.id, label: sub.heading, isTop: false })) ?? []),
    ]);

  return (
    <>
      {/* JSON-LD structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildArticleJsonLd(article)) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(buildBreadcrumbJsonLd(article)) }}
      />
      {faqJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
      )}
      <BlogDetailClient article={article} related={related} tocEntries={tocEntries} />
    </>
  );
}
