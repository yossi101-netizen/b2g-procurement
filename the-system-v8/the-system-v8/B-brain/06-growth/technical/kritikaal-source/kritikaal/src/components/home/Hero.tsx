"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { ArrowRight, Phone, Play } from "lucide-react";
import heroImage from "@/assets/hero-leather.jpg";
import { useTranslation } from "@/contexts/TranslationContext";
import { useState } from "react";

export const Hero = () => {
  const { t } = useTranslation();
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <section id="hero" className="relative min-h-[90vh] flex items-start pt-36 md:pt-48 pb-20 overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src={heroImage.src}
          alt="Leather craftsmanship"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-charcoal/95 via-charcoal/85 to-charcoal/60" />
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* LEFT — text content */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-2xl"
          >
            <span className="inline-block text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm mb-3 sm:mb-4">
              {t('hero.badge')}
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige leading-tight mb-4 sm:mb-6">
              {t('hero.title')} {" "}
              <span className="text-saddle-tan">{t('hero.titleHighlight')}</span>
            </h1>

            {/* Key Quote */}
            <div className="relative pl-4 sm:pl-6 border-l-4 border-saddle-tan mb-6 sm:mb-8">
              <blockquote className="font-serif text-base sm:text-lg md:text-xl lg:text-2xl text-warm-beige/90 italic font-medium leading-relaxed m-0">
                "{t('hero.quote')}"
              </blockquote>
            </div>

            {/* CTA Button */}
            <div className="mb-4 sm:mb-6">
              <Link href="/bookacall">
                <div className="leather-stitch-box inline-block">
                  <Button
                    size="xl"
                    className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-lora text-sm sm:text-base px-4 sm:px-6"
                  >
                    <Phone className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                    <span>{t('hero.ctaButton')}</span>
                    <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  </Button>
                </div>
              </Link>
            </div>

            {/* Supporting Text */}
            <p className="text-warm-beige/70 text-sm sm:text-base max-w-xl leading-relaxed">
              {t('hero.supportText').split(/(No sales pitch)/i).map((part, index) =>
                /No sales pitch/i.test(part) ? (
                  <span key={index} className="text-saddle-tan font-lora">{part}</span>
                ) : (
                  part
                )
              )}
            </p>
          </motion.div>

          {/* RIGHT — Founder video */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.9, delay: 0.3 }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative w-full max-w-[480px]">
              {/* Decorative border */}
              <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-saddle-tan/40 via-transparent to-saddle-tan/20 blur-sm" />

              <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-saddle-tan/25 bg-charcoal/80 backdrop-blur-sm">
                {/* Video thumbnail / player */}
                {!isPlaying ? (
                  <div
                    className="relative cursor-pointer group"
                    onClick={() => setIsPlaying(true)}
                    role="button"
                    aria-label="Play founder video"
                  >
                    {/* Thumbnail overlay */}
                    <div
                      className="w-full aspect-video bg-gradient-to-br from-[#3E2723] via-[#2C1810] to-[#1A0F0A]"
                      style={{
                        backgroundImage: `url('/hero-leather.jpg')`,
                        backgroundSize: "cover",
                        backgroundPosition: "center",
                      }}
                    />
                    {/* Dark overlay */}
                    <div className="absolute inset-0 bg-charcoal/60 group-hover:bg-charcoal/50 transition-colors duration-300" />

                    {/* Play button */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <motion.div
                        whileHover={{ scale: 1.12 }}
                        whileTap={{ scale: 0.96 }}
                        className="w-20 h-20 rounded-full bg-saddle-tan flex items-center justify-center shadow-[0_0_40px_rgba(212,165,116,0.5)] group-hover:shadow-[0_0_60px_rgba(212,165,116,0.7)] transition-shadow duration-300"
                      >
                        <Play className="w-8 h-8 text-charcoal ml-1" fill="currentColor" />
                      </motion.div>
                    </div>

                    {/* Caption */}
                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-charcoal via-charcoal/70 to-transparent">
                      <p className="font-serif italic text-warm-beige text-sm sm:text-base font-semibold">
                        Founder Video: Why Manufacturing Fails SMBs
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="w-full aspect-video bg-black flex items-center justify-center">
                    <p className="text-warm-beige/60 text-sm font-serif italic px-6 text-center">
                      Video coming soon - Our brand's production story starts here.
                    </p>
                  </div>
                )}
              </div>

              {/* Stitch decoration */}
              <div
                className="absolute -bottom-3 -right-3 w-24 h-24 opacity-20 pointer-events-none"
                style={{
                  backgroundImage:
                    "repeating-linear-gradient(45deg,#D4A574 0,#D4A574 2px,transparent 2px,transparent 10px)",
                }}
              />
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};
