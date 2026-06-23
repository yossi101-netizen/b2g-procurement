"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { useTranslation } from "@/contexts/TranslationContext";
import bgLeatherCertificate from "@/../public/leather-certificate-bg.webp";

// Import certification images
import sa8000 from "@/assets/certification/SAI Certificate.jpeg";

import lwg from "@/assets/certification/Leather working group certificate.jpeg";
import reach from "@/assets/certification/Reach Complaint Certificate.png";
import eudr from "@/assets/certification/EUDR certificate.jpeg";

export const CertificationStrip = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const { t } = useTranslation();

  const certifications = [
    {
      id: 1,
      title: t('certification.sa8000Title'),
      subtitle: t('certification.sa8000Subtitle'),
      image: sa8000,
      link: "https://sa-intl.org/",
    },

    {
      id: 4,
      title: t('certification.lwgTitle'),
      subtitle: t('certification.lwgSubtitle'),
      image: lwg,
      link: "https://www.leatherworkinggroup.com/",
    },
    {
      id: 5,
      title: t('certification.reachTitle'),
      subtitle: t('certification.reachSubtitle'),
      image: reach,
      link: "https://echa.europa.eu/regulations/reach/understanding-reach",
    },
    {
      id: 7,
      title: t('certification.eudrTitle'),
      subtitle: t('certification.eudrSubtitle'),
      image: eudr,
      link: "https://environment.ec.europa.eu/topics/forests/deforestation_en",
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut",
      },
    },
  };

  return (
    <section
      ref={ref}
      className="relative w-full overflow-hidden py-16 sm:py-20 lg:py-24"
    >
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src={bgLeatherCertificate.src}
          alt="Premium leather certification background"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-charcoal/95 via-charcoal/85 to-charcoal/70" />
      </div>
      {/* Content container */}
      <motion.div
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6"
        variants={containerVariants}
        initial="hidden"
        animate={isInView ? "visible" : "hidden"}
      >
        {/* Header */}
        <motion.div
          className="text-center mb-12 lg:mb-16"
          initial={{ opacity: 1, y: -20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: -20 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-block text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm mb-3 sm:mb-4">
            {t('certification.Badge') || 'Certified Excellence'}
          </span>
          <h2 className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige leading-tight mb-4 sm:mb-6">
            {t('certification.title')}
          </h2>
          <p className="text-warm-beige/70 text-sm sm:text-base md:text-lg max-w-3xl mx-auto leading-relaxed">
            {t('certification.subtitle')}
          </p>
        </motion.div>

        {/* Certifications grid */}
        <div className="flex flex-wrap justify-center items-center gap-4 sm:gap-5 md:gap-6">
          {certifications.map((cert) => (
            <motion.a
              key={cert.id}
              href={cert.link}
              target="_blank"
              rel="noopener noreferrer"
              variants={itemVariants}
              whileHover={{
                scale: 1.05,
                y: -5,
                transition: { duration: 0.2 },
              }}
              whileTap={{ scale: 0.98 }}
              className="w-full xs:w-[calc(50%-1rem)] sm:w-[calc(33.333%-1.25rem)] md:w-[calc(25%-1.5rem)] lg:w-[calc(20%-1.25rem)] max-w-[200px] group relative flex flex-col items-center justify-center p-3 sm:p-3 md:p-4 bg-gradient-to-br from-white/[0.08] to-white/[0.04] backdrop-blur-sm rounded-xl border border-saddle-tan/20 hover:border-saddle-tan/50 hover:bg-gradient-to-br hover:from-white/[0.14] hover:to-white/[0.07] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-saddle-tan/50 focus:ring-offset-2 focus:ring-offset-charcoal shadow-lg hover:shadow-[0_8px_30px_rgba(212,175,55,0.2)]"
            >
              {/* Glow effect on hover */}
              <div className="absolute inset-0 rounded-xl sm:rounded-2xl bg-gradient-to-br from-saddle-tan/0 to-amber-600/0 group-hover:from-saddle-tan/[0.1] group-hover:to-amber-600/[0.06] transition-all duration-500" />
              <div className="absolute -inset-[1px] rounded-xl sm:rounded-2xl bg-gradient-to-br from-saddle-tan/0 via-transparent to-amber-600/0 group-hover:from-saddle-tan/25 group-hover:to-amber-600/25 opacity-0 group-hover:opacity-100 blur-sm transition-all duration-500" />
              
              {/* Logo container */}
              <div className="relative w-full aspect-square mb-3 sm:mb-3 md:mb-4 rounded-lg sm:rounded-xl overflow-hidden bg-gradient-to-br from-warm-beige to-white shadow-inner group-hover:shadow-saddle-tan/30 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-saddle-tan/0 to-saddle-tan/5 group-hover:from-saddle-tan/[0.03] group-hover:to-saddle-tan/10 transition-all duration-300" />
                <img
                  src={cert.image.src}
                  alt={`${cert.title} - ${cert.subtitle}`}
                  className="relative w-full h-full object-contain p-2 sm:p-2 md:p-3 grayscale-[15%] group-hover:grayscale-0 group-hover:scale-110 transition-all duration-500"
                  loading="lazy"
                />
              </div>

              {/* Text content */}
              <div className="relative text-center space-y-1">
                <h3 className="text-warm-beige font-bold text-sm sm:text-sm md:text-base group-hover:text-saddle-tan transition-colors duration-300">
                  {cert.title}
                </h3>
                <p className="text-warm-beige/60 text-xs sm:text-xs leading-tight group-hover:text-warm-beige/80 transition-colors duration-300">
                  {cert.subtitle}
                </p>
              </div>

              {/* Subtle shine effect */}
              <div className="absolute inset-0 rounded-xl sm:rounded-2xl bg-gradient-to-tr from-transparent via-white/0 to-transparent group-hover:via-saddle-tan/[0.08] transition-all duration-700" />
              <div className="absolute top-0 right-0 w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-saddle-tan/0 to-transparent group-hover:from-saddle-tan/15 rounded-xl sm:rounded-2xl transition-all duration-500" />
            </motion.a>
          ))}
        </div>

        {/* Trust badge */}
        <motion.div
          className="mt-12 lg:mt-16 text-center"
          initial={{ opacity: 1 }}
          animate={isInView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 sm:gap-3 px-4 sm:px-5 py-2.5 sm:py-3 bg-gradient-to-r from-saddle-tan/10 via-saddle-tan/20 to-saddle-tan/10 border border-saddle-tan/30 rounded-full shadow-lg hover:shadow-saddle-tan/20 transition-all duration-300 group">
            <svg
              className="w-4 h-4 sm:w-5 sm:h-5 text-saddle-tan group-hover:text-warm-beige transition-colors duration-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <span className="text-warm-beige text-xs sm:text-sm font-semibold group-hover:text-saddle-tan transition-colors duration-300">
              {t('certification.verifiedBadge')}
            </span>
            <div className="w-2 h-2 rounded-full bg-saddle-tan animate-pulse" />
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
};

