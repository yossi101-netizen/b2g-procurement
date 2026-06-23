"use client";

import Link from "next/link";
import { ArrowRight, Calendar, Clock, User, ChevronRight, BookOpen } from "lucide-react";
import { type BlogArticle, type BlogSection } from "@/data/blogs";
import { useTranslation } from "@/contexts/TranslationContext";

function RenderSection({ section }: { section: BlogSection }) {
  return (
    <div id={section.id} className="mb-12 scroll-mt-40">
      {section.heading && (
        <h2 className="font-serif text-2xl md:text-3xl text-saddle-tan mb-6 leading-snug">
          {section.heading}
        </h2>
      )}

      {section.content && (
        <div className="space-y-4">
          {section.content.split("\n\n").map((para, i) => (
            <p key={i} className="text-white/80 leading-relaxed font-sans font-light text-base md:text-lg tracking-wide">
              {para}
            </p>
          ))}
        </div>
      )}

      {/* Subsections */}
      {section.subsections?.map((sub) => (
        <div key={sub.id} id={sub.id} className="mt-8 ml-0 md:ml-4 scroll-mt-40">
          <h3 className="font-serif text-xl md:text-2xl text-saddle-tan mb-4 leading-snug">
            {sub.heading}
          </h3>
          <div className="space-y-4">
            {sub.content.split("\n\n").map((para, i) => (
              <p key={i} className="text-white/80 leading-relaxed font-sans font-light text-base tracking-wide">
                {para}
              </p>
            ))}
          </div>
        </div>
      ))}

      {/* Table */}
      {section.table && (
        <div className="mt-6 overflow-x-auto rounded-xl border border-saddle-tan/20">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-saddle-tan/20 bg-[#1A0F0A]/60">
                {section.table.headers.map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left font-serif font-medium text-saddle-tan tracking-wide"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {section.table.rows.map((row, ri) => (
                <tr
                  key={ri}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors duration-200"
                >
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-3 text-white/80 font-sans font-light">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Bullet list */}
      {section.list && (
        <ul className="mt-6 space-y-3">
          {section.list.map((item, i) => {
            const [bold, ...rest] = item.split(":");
            const hasColon = item.includes(":");
            return (
              <li key={i} className="flex items-start gap-3">
                <span className="shrink-0 mt-2 w-1.5 h-1.5 rounded-full bg-saddle-tan" aria-hidden="true" />
                <p className="text-white/80 font-sans font-light text-base leading-relaxed">
                  {hasColon ? (
                    <>
                      <strong className="font-medium text-white">{bold}:</strong>
                      {rest.join(":")}
                    </>
                  ) : (
                    item
                  )}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default function BlogDetailClient({
  article,
  related,
  tocEntries,
}: {
  article: BlogArticle;
  related: BlogArticle[];
  tocEntries: { id: string; label: string; isTop: boolean }[];
}) {
  const { t, language } = useTranslation();

  const formattedDate = new Date(article.publishedDate).toLocaleDateString(language === "he" || language === "ar" ? language : "en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <>
      {/* ── HERO ── */}
      <section className="relative pt-48 pb-20 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src={article.image}
            alt={article.imageAlt}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 relative z-10 text-left">
          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex flex-wrap items-center gap-2 text-sm text-white/70">
              <li>
                <Link href="/" className="hover:text-saddle-tan transition-colors duration-200">
                  {t("nav.home")}
                </Link>
              </li>
              <li aria-hidden="true" className="text-saddle-tan/40">/</li>
              <li>
                <Link href="/blog" className="hover:text-saddle-tan transition-colors duration-200">
                  {t("nav.blog")}
                </Link>
              </li>
              <li aria-hidden="true" className="text-saddle-tan/40">/</li>
              <li className="text-saddle-tan font-medium" aria-current="page">
                {article.category}
              </li>
            </ol>
          </nav>

          {/* Category badge */}
          <span className="inline-block bg-saddle-tan text-white text-xs font-medium px-3 py-1 rounded-full tracking-wider uppercase mb-6">
            {article.category}
          </span>

          <h1 className="font-serif text-4xl md:text-5xl lg:text-7xl text-saddle-tan mt-0 mb-6 leading-tight max-w-4xl">
            {article.title}
          </h1>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-5 text-white/60 text-sm">
            <span className="flex items-center gap-2">
              <User className="w-4 h-4 text-saddle-tan" />
              <span className="text-white/90">{article.author}</span>
              <span className="text-white/40">— {article.authorTitle}</span>
            </span>
            <span className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-saddle-tan" />
              {formattedDate}
            </span>
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-saddle-tan" />
              {article.readTime} min
            </span>
          </div>

          <div className="mt-12 w-32 h-[1px] bg-saddle-tan/40" />
        </div>
      </section>

      {/* ── ARTICLE BODY ── */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img src={article.image} alt="" aria-hidden="true" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="grid lg:grid-cols-[1fr_280px] gap-12 max-w-6xl mx-auto">

            {/* ── Main content column ── */}
            <article className="min-w-0">
              {article.sections.map((section) => (
                <RenderSection key={section.id} section={section} />
              ))}

              {/* ── FAQ Section ── */}
              {article.faqs && article.faqs.length > 0 && (
                <div className="mt-16 pt-12 border-t border-saddle-tan/20">
                  <h2 className="font-serif text-2xl md:text-3xl text-saddle-tan mb-8 leading-snug">
                    {t("blog.frequentlyAsked")}
                  </h2>
                  <div className="space-y-4">
                    {article.faqs.map((faq, i) => (
                      <details
                        key={i}
                        className="group border border-saddle-tan/20 rounded-xl overflow-hidden bg-[#1A0F0A]/40 hover:border-saddle-tan/40 transition-all duration-300"
                      >
                        <summary className="flex items-center justify-between gap-4 px-6 py-5 cursor-pointer list-none">
                          <span className="font-serif text-base md:text-lg text-white group-hover:text-saddle-tan transition-colors duration-300 leading-snug">
                            {faq.question}
                          </span>
                          <ChevronRight className="w-4 h-4 shrink-0 text-saddle-tan group-open:rotate-90 transition-transform duration-300" />
                        </summary>
                        <div className="px-6 pb-5 pt-0">
                          <div className="h-px bg-saddle-tan/20 mb-4" />
                          <p className="text-white/70 font-sans font-light text-sm leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </details>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Tags ── */}
              <div className="mt-12 pt-8 border-t border-saddle-tan/20">
                <p className="text-white/50 text-xs uppercase tracking-widest mb-3">{t("blog.tags")}</p>
                <div className="flex flex-wrap gap-2">
                  {article.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 rounded-full border border-saddle-tan/30 text-saddle-tan/80 text-xs font-medium tracking-wide"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* ── Author box ── */}
              <div className="mt-12 p-6 rounded-2xl border border-saddle-tan/20 bg-[#1A0F0A]/40">
                <p className="text-white/50 text-xs uppercase tracking-widest mb-3">{t("blog.aboutAuthor")}</p>
                <p className="font-serif text-lg text-white mb-1">{article.author}</p>
                <p className="text-saddle-tan text-sm mb-3">{article.authorTitle}</p>
                <p className="text-white/70 text-sm font-sans font-light leading-relaxed">
                  Yossi Daniel has hands-on experience with overseas leather manufacturing since 2012,
                  including direct production management in China — which exposed the structural accountability
                  gap that KRITIKAAL was built to solve.
                </p>
              </div>
            </article>

            {/* ── Table of contents sidebar ── */}
            {tocEntries.length > 0 && (
              <aside className="hidden lg:block" aria-label="Table of contents">
                <div className="sticky top-40">
                  <div className="rounded-2xl border border-saddle-tan/20 bg-[#1A0F0A]/60 p-6">
                    <p className="text-saddle-tan font-medium tracking-widest uppercase text-xs mb-4">
                      {t("blog.inThisArticle")}
                    </p>
                    <nav>
                      <ul className="space-y-2">
                        {tocEntries.map((entry) => (
                          <li key={entry.id}>
                            <a
                              href={`#${entry.id}`}
                              className={`block text-sm leading-relaxed transition-colors duration-200 hover:text-saddle-tan ${
                                entry.isTop
                                  ? "text-white/70 font-medium"
                                  : "text-white/50 pl-3 font-light"
                              }`}
                            >
                              {entry.label}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </nav>
                  </div>

                  {/* Sidebar CTA */}
                  <div className="mt-4 rounded-2xl border border-saddle-tan/20 bg-[#1A0F0A]/60 p-6">
                    <p className="text-white font-serif text-base mb-2 leading-snug">
                      {t("blog.sidebarCta")}
                    </p>
                    <p className="text-white/60 text-xs mb-4 font-light leading-relaxed">
                      {t("blog.sidebarCtaDesc")}
                    </p>
                    <Link
                      href="/bookacall"
                      className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg bg-saddle-tan hover:bg-[#C49464] text-white font-serif font-medium text-sm transition-all duration-300"
                    >
                      {t("blog.sidebarCtaButton")}
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </aside>
            )}
          </div>
        </div>
      </section>

      {/* ── RELATED ARTICLES ── */}
      {related.length > 0 && (
        <section className="relative py-16 overflow-hidden">
          <div className="absolute inset-0 z-0">
            <img src={article.image} alt="" aria-hidden="true" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-charcoal/90" />
          </div>

          <div className="container mx-auto px-4 relative z-10">
            <p className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-3">
              {t("blog.continueReading")}
            </p>
            <h2 className="font-serif text-3xl text-white mb-10">{t("blog.relatedArticles")}</h2>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {related.map((rel) => {
                const relDate = new Date(rel.publishedDate).toLocaleDateString(language === "he" || language === "ar" ? language : "en-GB", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                });
                return (
                <Link
                  key={rel.slug}
                  href={`/blog/${rel.slug}`}
                  className="group block rounded-2xl overflow-hidden border border-saddle-tan/20 hover:border-saddle-tan/50 transition-all duration-500 relative hover:shadow-[0_8px_32px_rgba(212,165,116,0.12)]"
                  aria-label={`${t("blog.readArticle")}: ${rel.title}`}
                >
                  {/* Background similar to Hero */}
                  <div className="absolute inset-0 z-0">
                    <img
                      src="/leather-bg.jpg"
                      alt=""
                      aria-hidden="true"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-charcoal/90 group-hover:bg-[#2C1810]/80 transition-colors duration-500" />
                  </div>

                  <div className="relative z-10 flex flex-col h-full">
                    {/* Card image */}
                    <div className="relative h-48 overflow-hidden shrink-0">
                      <img
                        src={rel.image}
                        alt={rel.imageAlt}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-charcoal/80 to-transparent" />
                      <div className="absolute top-3 left-3">
                        <span className="bg-saddle-tan/90 text-white text-xs font-medium px-2.5 py-1 rounded-full tracking-wider uppercase">
                          {rel.category}
                        </span>
                      </div>
                    </div>

                    {/* Card body */}
                    <div className="p-6 flex flex-col flex-grow">
                      <div className="flex items-center gap-3 text-white/40 text-xs mb-3">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {relDate}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {rel.readTime} min
                        </span>
                      </div>

                      <h3 className="font-serif text-lg text-white group-hover:text-saddle-tan transition-colors duration-300 leading-snug mb-3">
                        {rel.title}
                      </h3>

                      <p className="text-white/60 text-sm leading-relaxed mb-5 line-clamp-2">
                        {rel.excerpt}
                      </p>

                      <div className="mt-auto flex items-center gap-2 text-saddle-tan text-sm font-serif font-medium group-hover:gap-3 transition-all duration-300">
                        <BookOpen className="w-3.5 h-3.5" />
                        {t("blog.readArticle")}
                      </div>
                    </div>
                  </div>
                </Link>
              )})}
            </div>
          </div>
        </section>
      )}

      {/* ── BOTTOM CTA ── */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img src="/leather form bg.webp" alt="" aria-hidden="true" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <div className="max-w-2xl mx-auto">
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
              {t("blog.ctaBrandBadge")}
            </span>
            <h2 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mt-4 mb-6 leading-tight">
              {t("blog.ctaTitle")}{" "}
              <span className="text-saddle-tan">{t("blog.ctaTitleHighlight")}</span>
            </h2>
            <p className="text-white/80 mb-10 text-lg leading-relaxed">
              {t("blog.ctaSubtitle")}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <div className="leather-stitch-box inline-block">
                <Link
                  href="/bookacall"
                  className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg bg-saddle-tan hover:bg-[#C49464] text-white font-serif font-medium text-base transition-all duration-300 shadow-md"
                >
                  {t("blog.ctaButton")}
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
              <Link
                href="/blog"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg border border-saddle-tan text-saddle-tan font-serif font-medium text-base hover:bg-saddle-tan/10 transition-all duration-300"
              >
                {t("blog.ctaBackToBlog")}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
