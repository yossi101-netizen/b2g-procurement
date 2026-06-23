"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Calendar, Clock } from "lucide-react";
import { blogArticles } from "@/data/blogs";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";

export const HomeBlog = () => {
  const { t } = useTranslation();
  const featured = blogArticles.slice(0, 3);

  return (
    <section className="relative py-20 sm:py-24 overflow-hidden bg-charcoal">
      {/* Background Image */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
        <div className="absolute inset-0 bg-charcoal/90" />
      </div>

      {/* Ambient leather glow */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-saddle-tan/5 blur-[140px] rounded-full pointer-events-none z-0" />

      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        {/* Header */}
        <motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.6 }}
  className="flex flex-col items-center justify-center text-center gap-6 mb-12"
>
  <div className="max-w-2xl mx-auto">
    <span className="inline-block text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm mb-3">
      From the Journal
    </span>

    <h2 className="font-serif text-3xl sm:text-4xl md:text-5xl text-warm-beige leading-tight">
      Leather Intelligence
    </h2>

    <p className="text-warm-beige/60 mt-4 text-sm sm:text-base max-w-lg mx-auto">
      Compliance, quality, and supply chain insights for global leather brands.
    </p>
  </div>

  <Link
    href="/blog"
    className="inline-flex items-center gap-2 text-saddle-tan font-serif font-medium text-sm sm:text-base hover:gap-3 transition-all duration-300 group border border-saddle-tan/30 hover:border-saddle-tan/60 px-5 py-2.5 rounded-full"
  >
    View All Articles

    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
  </Link>
</motion.div>

        {/* Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
          {featured.map((article, i) => (
            <motion.div
              key={article.slug}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            >
              <Link
                href={`/blog/${article.slug}`}
                className="group flex flex-col h-full rounded-2xl overflow-hidden border border-saddle-tan/15 hover:border-saddle-tan/45 transition-all duration-500 bg-gradient-to-br from-white/[0.05] to-white/[0.02] hover:shadow-[0_8px_40px_rgba(212,165,116,0.12)] backdrop-blur-sm"
              >
                {/* Image */}
                <div className="relative h-44 overflow-hidden shrink-0">
                  <img
                    src={article.image}
                    alt={article.imageAlt}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-charcoal/80 via-charcoal/20 to-transparent" />
                  <span className="absolute top-3 left-3 bg-saddle-tan/90 text-white text-xs font-medium px-2.5 py-1 rounded-full tracking-wider uppercase">
                    {article.category}
                  </span>
                </div>

                {/* Body */}
                <div className="flex flex-col flex-grow p-5 sm:p-6">
                  <div className="flex items-center gap-3 text-warm-beige/40 text-xs mb-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(article.publishedDate).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {article.readTime} min
                    </span>
                  </div>

                  <h3 className="font-serif text-base sm:text-lg text-warm-beige group-hover:text-saddle-tan transition-colors duration-300 leading-snug mb-2 line-clamp-2">
                    {article.title}
                  </h3>

                  <p className="text-warm-beige/55 text-sm leading-relaxed mb-4 line-clamp-2 flex-grow">
                    {article.excerpt}
                  </p>

                  <div className="flex items-center gap-2 text-saddle-tan text-xs sm:text-sm font-serif font-medium group-hover:gap-3 transition-all duration-300 mt-auto">
                    <BookOpen className="w-3.5 h-3.5" />
                    Read Article
                    <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 -ml-1 group-hover:ml-0 transition-all duration-300" />
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          className="mt-12 text-center"
        >
          <Link
            href="/blog"
            className="inline-flex items-center gap-2 text-warm-beige/70 hover:text-saddle-tan text-sm transition-colors duration-300 group"
          >
            <span className="underline underline-offset-4 decoration-saddle-tan/30 group-hover:decoration-saddle-tan transition-all duration-300">
              Browse all {blogArticles.length} articles on leather manufacturing
            </span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
};
