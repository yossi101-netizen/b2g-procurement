"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, HelpCircle, ArrowRight } from "lucide-react";
import Link from "next/link";
import { faqData, homepageFaqData, type FAQItem } from "@/data/faqData";
import { useTranslation } from "@/contexts/TranslationContext";

interface FAQProps {
  /** When true, renders all 29 FAQs (for /faq page). When false, renders first 8 (homepage). */
  showAll?: boolean;
  /** Hide the "View all FAQs" CTA — useful on the dedicated /faq page */
  hideCta?: boolean;
}

const FAQAccordionItem = ({
  item,
  index,
  isOpen,
  onToggle,
}: {
  item: FAQItem;
  index: number;
  isOpen: boolean;
  onToggle: () => void;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      className="border border-[#D4A574]/20 rounded-2xl overflow-hidden bg-transparent backdrop-blur-sm hover:bg-[#2C1810]/40 hover:border-[#D4A574]/50 transition-all duration-300 shadow-lg"
    >
      <button
        id={`faq-btn-${item.id}`}
        aria-expanded={isOpen}
        aria-controls={`faq-panel-${item.id}`}
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left group cursor-pointer"
      >
        {/* Question number badge */}
        <span
          className="shrink-0 w-10 h-10 rounded-full bg-[#1A0F0A]/90 border border-[#D4A574]/40 
            text-[#D4A574] text-sm font-serif font-medium flex items-center justify-center 
            group-hover:border-[#D4A574] group-hover:bg-[#2C1810] transition-all duration-300 shadow-md"
          aria-hidden="true"
        >
          {String(index + 1).padStart(2, "0")}
        </span>

        {/* Question text */}
        <span className="flex-1 font-serif text-lg md:text-xl text-white/90 group-hover:text-white transition-colors duration-300 leading-relaxed font-medium">
          {item.question}
        </span>

        {/* Toggle icon */}
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="shrink-0"
          aria-hidden="true"
        >
          <ChevronDown
            className={`w-5 h-5 transition-colors duration-300 ${
              isOpen ? "text-[#D4A574]" : "text-[#D4A574]/60 group-hover:text-[#D4A574]"
            }`}
          />
        </motion.span>
      </button>

      {/* Answer panel */}
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id={`faq-panel-${item.id}`}
            role="region"
            aria-labelledby={`faq-btn-${item.id}`}
            key="answer"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
            style={{ overflow: "hidden" }}
          >
            {/* Stitch divider */}
            <div
              className="mx-6 h-[1px]"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg,#D4A574 0,#D4A574 6px,transparent 6px,transparent 12px)",
                opacity: 0.35,
              }}
            />
            <div className="px-6 py-5 pl-[4.5rem]">
              <p className="text-white/70 leading-relaxed font-sans text-sm md:text-base tracking-wide">
                {item.answer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export const FAQ = ({ showAll = false, hideCta = false }: FAQProps) => {
  const items = showAll ? faqData : homepageFaqData;
  const [openId, setOpenId] = useState<string | null>(null);

  const toggle = (id: string) => setOpenId((prev) => (prev === id ? null : id));

  const { t } = useTranslation();

  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background layer */}
      <div className="absolute inset-0 z-0">
        <img
          src="/leather-bg.jpg"
          alt="Leather texture background"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-charcoal/90" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
              {t("faq.badge")}
            </span>
            <h2 className="font-serif text-4xl md:text-5xl lg:text-7xl text-white mt-4 mb-6 leading-tight">
              {t("faq.title")} <span className="text-saddle-tan">{t("faq.titleHighlight")}</span>
            </h2>
            <p className="text-white/80 max-w-2xl mx-auto text-lg leading-relaxed">
              {t("faq.subtitle")}
            </p>
          </motion.div>
        </div>

        {/* Accordion list */}
        <div className="max-w-4xl mx-auto flex flex-col gap-3">
          {items.map((item, index) => (
            <FAQAccordionItem
              key={item.id}
              item={item}
              index={index}
              isOpen={openId === item.id}
              onToggle={() => toggle(item.id)}
            />
          ))}
        </div>

        {/* CTA — View all / Book a call */}
        {!hideCta && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16 text-center space-y-6"
          >
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              {/* Book Call Button */}
              <div className="leather-stitch-box">
                <Link href="/bookacall">
                  <button className="bg-saddle-tan hover:bg-[#C49464] text-white px-8 py-4 font-serif font-medium transition-all duration-300 w-full sm:w-auto hover:shadow-[0_0_20px_rgba(212,165,116,0.3)]">
                    {t("faq.bookCall")}
                  </button>
                </Link>
              </div>

              {/* View all FAQs Button */}
              {!showAll && (
                <Link
                  href="/faq"
                  className="text-white/70 hover:text-saddle-tan font-sans font-light flex items-center gap-2 group transition-colors duration-300"
                >
                  {t("faq.viewAllFaqs")}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </section>
  );
};
