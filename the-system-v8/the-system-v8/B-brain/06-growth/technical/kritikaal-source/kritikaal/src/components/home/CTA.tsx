"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowRight, Phone } from "lucide-react";
import { useTranslation } from "@/contexts/TranslationContext";


export const CTA = () => {
  const { t } = useTranslation();
  return (
    <section id="contact" className="relative py-16 sm:py-20 md:py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 z-0">
        <img
          src="/leather-bg.avif"
          alt="Manufacturing facility"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-charcoal/95 via-charcoal/90 to-charcoal/80" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
              {t('cta.badge')}
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige mt-3 sm:mt-4 mb-4 sm:mb-6 leading-tight">
      {t('cta.title')} <span className="text-saddle-tan">{t('cta.titleHighlight')}</span> {t('cta.titleEnd')}
    </h2>
            <p className="text-base sm:text-lg text-warm-beige/80 mb-6 sm:mb-10 max-w-2xl mx-auto font-serif font-extralight tracking-wide">
              {t('cta.description')}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/bookacall">
                <div className="leather-stitch-box inline-block">
                  <Button className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal text-sm sm:text-base" size="lg">
                    <Phone className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                    {t('cta.ctaButton')}
                    <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 ml-2" />
                  </Button>
                </div>
              </Link>
            
            </div>

            <p className="mt-6 sm:mt-8 text-warm-beige/60 text-xs sm:text-sm px-2 font-serif font-light tracking-wider">
              {t('cta.supportText')}
            </p>

            
             <div className="mt-10 mb-4 flex justify-center">
  <blockquote className="font-serif relative pl-6 border-l-4 border-saddle-tan text-saddle-tan italic 
    text-base md:text-lg lg:text-xl 
    tracking-wider font-light">
    "{t('cta.quote')}"
  </blockquote>
</div>
</motion.div>
      </div>
      </div>
    </section>
  );
};
