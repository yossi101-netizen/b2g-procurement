"use client";

import Link from "next/link";
import { blogArticles } from "@/data/blogs";
import { Calendar, Clock, ArrowRight, BookOpen } from "lucide-react";
import { useTranslation } from "@/contexts/TranslationContext";

export default function BlogClient() {
  const { t, language } = useTranslation();

  return (
    <>
      {/* ── HERO ── */}
      <section className="relative pt-48 pb-20 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt="Leather manufacturing knowledge"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 relative z-10 text-left">
          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex items-center gap-2 text-sm text-white/70">
              <li>
                <Link href="/" className="hover:text-saddle-tan transition-colors duration-200">
                  {t("nav.home")}
                </Link>
              </li>
              <li aria-hidden="true" className="text-saddle-tan/40">/</li>
              <li className="text-saddle-tan font-medium" aria-current="page">
                {t("nav.blog")}
              </li>
            </ol>
          </nav>

          <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
            {t("blog.badge")}
          </span>

          <h1 className="font-serif text-5xl md:text-6xl lg:text-8xl text-white mt-4 mb-6 leading-tight max-w-4xl">
            {t("blog.heroTitle")}{" "}
            <span className="text-saddle-tan">{t("blog.heroTitleHighlight")}</span>
          </h1>

          <p className="text-white/90 max-w-2xl text-lg md:text-xl font-sans font-light tracking-wide leading-relaxed">
            {t("blog.heroSubtitle")}
          </p>

          {/* Stats */}
          <div className="mt-12 flex flex-wrap gap-10 md:gap-16">
            {[
              { value: String(blogArticles.length), label: t("blog.stat1Label") },
              { value: t("blog.stat2Value"), label: t("blog.stat2Label") },
              { value: t("blog.stat3Value"), label: t("blog.stat3Label") },
              { value: t("blog.stat4Value"), label: t("blog.stat4Label") },
            ].map((stat) => (
              <div key={stat.label} className="text-left">
                <div className="font-serif text-4xl font-light text-saddle-tan">{stat.value}</div>
                <div className="text-white/60 text-xs mt-1 uppercase tracking-widest">{stat.label}</div>
              </div>
            ))}
          </div>

          <div className="mt-16 w-32 h-[1px] bg-saddle-tan/40" />
        </div>
      </section>

      {/* ── ARTICLE GRID ── */}
      <section className="relative py-16 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt=""
            aria-hidden="true"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <p className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-10">
            {t("blog.allArticles")}
          </p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {blogArticles.map((article) => {
              // Only format dates in en-GB, but could also adapt to locale format
              const formattedDate = new Date(article.publishedDate).toLocaleDateString(language === "he" || language === "ar" ? language : "en-GB", {
                day: "numeric",
                month: "short",
                year: "numeric",
              });
              
              return (
              <Link
                key={article.slug}
                href={`/blog/${article.slug}`}
                className="group block rounded-2xl overflow-hidden border border-saddle-tan/20 hover:border-saddle-tan/50 transition-all duration-500 relative hover:shadow-[0_8px_32px_rgba(212,165,116,0.12)]"
                aria-label={`${t("blog.readArticle")}: ${article.title}`}
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
                      src={article.image}
                      alt={article.imageAlt}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-charcoal/80 to-transparent" />
                    <div className="absolute top-3 left-3">
                      <span className="bg-saddle-tan/90 text-white text-xs font-medium px-2.5 py-1 rounded-full tracking-wider uppercase">
                        {article.category}
                      </span>
                    </div>
                  </div>

                  {/* Card body */}
                  <div className="p-6 flex flex-col flex-grow">
                    <div className="flex items-center gap-3 text-white/40 text-xs mb-3">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formattedDate}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {article.readTime} min
                      </span>
                    </div>

                    <h3 className="font-serif text-lg text-white group-hover:text-saddle-tan transition-colors duration-300 leading-snug mb-3">
                      {article.title}
                    </h3>

                    <p className="text-white/60 text-sm leading-relaxed mb-5 line-clamp-2">
                      {article.excerpt}
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

      {/* ── BOTTOM CTA ── */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img src="/leather form bg.webp" alt="" aria-hidden="true" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <div className="max-w-2xl mx-auto">
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
              {t("blog.ctaBadge")}
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
                href="/faq"
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg border border-saddle-tan text-saddle-tan font-serif font-medium text-base hover:bg-saddle-tan/10 transition-all duration-300"
              >
                {t("blog.ctaSecondary")}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
