"use client";

import { useTranslation } from "@/contexts/TranslationContext";
import { FAQ } from "@/components/home/FAQ";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export default function FAQClient() {
  const { t } = useTranslation();

  return (
    <>
      {/* Page hero */}
      <section className="relative pt-48 pb-20 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt="Leather craftsmanship"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 relative z-10 text-left">
          {/* Breadcrumb */}
          <nav aria-label="Breadcrumb" className="mb-8">
            <ol className="flex items-center justify-start gap-2 text-sm text-white/70">
              <li>
                <Link
                  href="/"
                  className="hover:text-saddle-tan transition-colors duration-200"
                >
                  {t("nav.home")}
                </Link>
              </li>
              <li aria-hidden="true" className="text-saddle-tan/40">
                /
              </li>
              <li
                className="text-saddle-tan font-medium"
                aria-current="page"
              >
                FAQ
              </li>
            </ol>
          </nav>

          <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
            {t("faq.heroBadge")}
          </span>

          <h1 className="font-serif text-5xl md:text-6xl lg:text-8xl text-white mt-4 mb-6 leading-tight max-w-4xl">
            {t("faq.heroTitle")}{" "}
            <span className="text-saddle-tan">{t("faq.heroTitleHighlight")}</span>
          </h1>

          <p className="text-white/90 max-w-2xl text-lg md:text-xl font-sans font-light tracking-wide leading-relaxed">
            {t("faq.heroSubtitle")}
          </p>

          {/* Stats row */}
          <div className="mt-12 flex flex-wrap justify-start gap-10 md:gap-16">
            {[
              { value: t("faq.stat1Value"), label: t("faq.stat1Label") },
              { value: t("faq.stat2Value"), label: t("faq.stat2Label") },
              { value: t("faq.stat3Value"), label: t("faq.stat3Label") },
              { value: t("faq.stat4Value"), label: t("faq.stat4Label") },
            ].map((stat) => (
              <div key={stat.label} className="text-left">
                <div className="font-serif text-4xl font-light text-saddle-tan">
                  {stat.value}
                </div>
                <div className="text-white/60 text-xs mt-1 uppercase tracking-widest">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Decorative line */}
          <div
            className="mt-16 w-32 h-[1px] bg-saddle-tan/40"
          />
        </div>
      </section>

      {/* All 29 FAQs */}
      <FAQ showAll={true} hideCta={true} />

      {/* Bottom CTA */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt="Leather craftsmanship"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        <div className="container mx-auto px-4 text-center relative z-10">
          <div className="max-w-2xl mx-auto">
            <h2 className="font-serif text-4xl md:text-5xl lg:text-7xl text-white mt-4 mb-6 leading-tight">
              {t("faq.ctaTitle")}{" "}
              <span className="text-saddle-tan">{t("faq.ctaTitleHighlight")}</span>
            </h2>

            <p className="text-white/80 mb-6 mx-auto text-lg leading-relaxed">
              {t("faq.ctaSubtitle")}
            </p>

            <p className="text-saddle-tan font-medium mb-10 tracking-widest uppercase text-sm">
              {t("faq.ctaBadge")}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <div className="leather-stitch-box inline-block">
                <Link href="/bookacall">
                  <Button
                    className="bg-saddle-tan hover:bg-[#C49464] text-white font-serif font-medium"
                    size="lg"
                  >
                    {t("faq.ctaButton")}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
