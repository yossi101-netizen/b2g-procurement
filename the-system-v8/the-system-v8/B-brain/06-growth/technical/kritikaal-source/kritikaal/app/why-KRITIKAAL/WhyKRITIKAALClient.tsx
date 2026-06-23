"use client";


import { motion } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ArrowRight, Check, Lock, Settings, Package, Shield, X } from "lucide-react";
import { useState } from "react";
import { FiUser, FiLock, FiSearch, FiDollarSign } from "react-icons/fi";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";

/* -------------------- DATA -------------------- */

const WhyKRITIKAAL = () => {
  const { t } = useTranslation();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const manufacturingControls = [
    {
      stage: t('whyKRITIKAALPage.lockStage'),
      icon: Lock,
      color: "from-saddle-tan/20 to-saddle-tan/10",
      borderColor: "border-saddle-tan/40",
      tagColor: "bg-saddle-tan/20 text-saddle-tan",
      iconColor: "text-saddle-tan",
      items: [
        { tag: t('whyKRITIKAALPage.lockItem1Tag'), title: t('whyKRITIKAALPage.lockItem1Title'), desc: t('whyKRITIKAALPage.lockItem1Desc') },
        { tag: t('whyKRITIKAALPage.lockItem2Tag'), title: t('whyKRITIKAALPage.lockItem2Title'), desc: t('whyKRITIKAALPage.lockItem2Desc') },
        { tag: t('whyKRITIKAALPage.lockItem3Tag'), title: t('whyKRITIKAALPage.lockItem3Title'), desc: t('whyKRITIKAALPage.lockItem3Desc') },
      ],
    },
    {
      stage: t('whyKRITIKAALPage.controlStage'),
      icon: Settings,
      color: "from-deep-leather-brown/20 to-deep-leather-brown/10",
      borderColor: "border-deep-leather-brown/40",
      tagColor: "bg-deep-leather-brown/20 text-deep-leather-brown",
      iconColor: "text-deep-leather-brown",
      items: [
        { tag: t('whyKRITIKAALPage.controlItem1Tag'), title: t('whyKRITIKAALPage.controlItem1Title'), desc: t('whyKRITIKAALPage.controlItem1Desc') },
        { tag: t('whyKRITIKAALPage.controlItem2Tag'), title: t('whyKRITIKAALPage.controlItem2Title'), desc: t('whyKRITIKAALPage.controlItem2Desc') },
        { tag: t('whyKRITIKAALPage.controlItem3Tag'), title: t('whyKRITIKAALPage.controlItem3Title'), desc: t('whyKRITIKAALPage.controlItem3Desc') },
      ],
    },
    {
      stage: t('whyKRITIKAALPage.deliverStage'),
      icon: Package,
      color: "from-charcoal/20 to-charcoal/10",
      borderColor: "border-charcoal/40",
      tagColor: "bg-charcoal/20 text-charcoal",
      iconColor: "text-charcoal",
      items: [
        { tag: t('whyKRITIKAALPage.deliverItem1Tag'), title: t('whyKRITIKAALPage.deliverItem1Title'), desc: t('whyKRITIKAALPage.deliverItem1Desc') },
        { tag: t('whyKRITIKAALPage.deliverItem2Tag'), title: t('whyKRITIKAALPage.deliverItem2Title'), desc: t('whyKRITIKAALPage.deliverItem2Desc') },
        { tag: t('whyKRITIKAALPage.deliverItem3Tag'), title: t('whyKRITIKAALPage.deliverItem3Title'), desc: t('whyKRITIKAALPage.deliverItem3Desc') },
      ],
    },
  ];

  const steps = [
    {
      title: t('whyKRITIKAALPage.escrowStep1Title'),
      desc: t('whyKRITIKAALPage.escrowStep1Desc'),
      color: "#2C1810",
      icon: FiUser,
      borderColor: "#F5E6D3",
    },
    {
      title: t('whyKRITIKAALPage.escrowStep2Title'),
      desc: t('whyKRITIKAALPage.escrowStep2Desc'),
      color: "#D4A574",
      icon: FiLock,
      borderColor: "#2C1810",
    },
    {
      title: t('whyKRITIKAALPage.escrowStep3Title'),
      desc: t('whyKRITIKAALPage.escrowStep3Desc'),
      color: "#F5E6D3",
      icon: FiSearch,
      borderColor: "#D4A574",
    },
    {
      title: t('whyKRITIKAALPage.escrowStep4Title'),
      desc: t('whyKRITIKAALPage.escrowStep4Desc'),
      color: "#4E342E",
      icon: FiDollarSign,
      borderColor: "#F5E6D3",
    },
  ];
  
  const notManufactured = [
    { item: t('whyKRITIKAALPage.syntheticLeather'), icon: Shield },
    { item: t('whyKRITIKAALPage.fastFashion'), icon: Package },
    { item: t('whyKRITIKAALPage.experimental'), icon: Settings },
  ];

/* PAGE */

  return (
    <>
      {/* Hero Section - Standing Out in the Crowd */}
      <section className="relative pt-32 pb-32 lg:pt-48 lg:pb-48 overflow-hidden min-h-[70vh] flex items-center">

        {/* Image Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
          <div className="absolute inset-0 bg-charcoal/85" />
        </div>
        
        {/* Noise Texture */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
        
        <div className="container mx-auto px-4 relative z-10">
          
          {/* Desktop Layout - Side by side */}
          <div className="hidden lg:grid lg:grid-cols-2 gap-16 items-center max-w-7xl mx-auto">
            
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 1, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center lg:text-left"
            >
              <motion.span 
                initial={{ opacity: 1, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-6 block"
              >
                {t('whyKRITIKAALPage.badge')}
              </motion.span>

              <motion.h1
                className="text-4xl md:text-5xl lg:text-6xl text-warm-beige mb-6 leading-tight"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
                {t('whyKRITIKAALPage.title')} <span className="text-saddle-tan font-serif font-medium">{t('whyKRITIKAALPage.titleHighlight')}</span>
              </motion.h1>
              
              <motion.p
                className="text-xl text-warm-beige/80 leading-relaxed mb-10"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                {t('whyKRITIKAALPage.subtitle')}
              </motion.p>
            </motion.div>
          </div>

          {/* Mobile Layout - Stacked */}
          <div className="lg:hidden space-y-10">
            
            {/* Hero Title Section */}
            <motion.div
              initial={{ opacity: 1, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center"
            >
              <motion.span 
                initial={{ opacity: 1, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-6 block"
              >
                {t('whyKRITIKAALPage.badge')}
              </motion.span>

              <motion.h1
                className="text-4xl md:text-5xl text-warm-beige mb-6 leading-tight"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
                {t('whyKRITIKAALPage.title')} <span className="text-saddle-tan font-serif font-medium">{t('whyKRITIKAALPage.titleHighlight')}</span>
              </motion.h1>
              
              <motion.p
                className="text-xl text-warm-beige/80 leading-relaxed"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                {t('whyKRITIKAALPage.subtitle')}
              </motion.p>
            </motion.div>

            {/* Mobile stats */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { number: "300+", label: "Min order units" },
                { number: "AQL 2.5", label: "Quality standard" },
                { number: "45–65d", label: "Production timeline" },
                { number: "0%", label: "UK import duty" },
              ].map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + i * 0.1 }}
                  className="text-center p-4 rounded-xl bg-white/[0.05] border border-saddle-tan/15"
                >
                  <div className="font-serif text-2xl font-light text-saddle-tan">{stat.number}</div>
                  <div className="text-warm-beige/70 text-xs mt-1">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* MANUFACTURING CONTROLS */}
      <section className="py-24 bg-warm-beige">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
              {t('whyKRITIKAALPage.controlsBadge')}
            </span>
            <h2 className=" text-4xl md:text-5xl text-charcoal mt-4 mb-4">{t('whyKRITIKAALPage.controlsTitle')}</h2>
            <p className="text-charcoal/70 mt-4 max-w-2xl mx-auto">{t('whyKRITIKAALPage.controlsSubtitle')}</p>
          </motion.div>

          {/* Streamlined Timeline View - All Three Stages */}
          <div className="max-w-6xl mx-auto">
            {/* Timeline Connector */}
            <div className="hidden lg:flex items-center justify-center mb-8">
              <div className="flex items-center gap-4">
                {manufacturingControls.map((block, index) => (
                  <div key={block.stage} className="flex items-center">
                    <motion.div
                      initial={{ opacity: 1, scale: 0.8 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: index * 0.2 }}
                      className={`w-16 h-16 rounded-full flex items-center justify-center border-2 ${
                        index === 0 ? "bg-saddle-tan border-saddle-tan" : index === 1 ? "bg-deep-leather-brown border-deep-leather-brown" : "bg-charcoal border-charcoal"
                      }`}
                    >
                      <block.icon className="w-8 h-8 text-warm-beige" />
                    </motion.div>
                    {index < manufacturingControls.length - 1 && (
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: 120 }}
                        viewport={{ once: true }}
                        transition={{ delay: index * 0.2 + 0.3, duration: 0.5 }}
                        className="h-1 bg-gradient-to-r from-saddle-tan via-deep-leather-brown to-charcoal mx-2"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* All Three Stages Grid */}
            <div className="grid lg:grid-cols-3 gap-8">
              {manufacturingControls.map((block, blockIndex) => (
                <motion.div
                  key={block.stage}
                  initial={{ opacity: 1, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: blockIndex * 0.15 }}
                  className="space-y-6"
                >
                  {/* Stage Header */}
                  <div className={`flex items-center gap-3 p-4 rounded-2xl bg-gradient-to-r ${block.color} border ${block.borderColor}`}>
                    <block.icon className={`w-6 h-6 ${block.iconColor}`} />
                    <h3 className=" text-2xl text-charcoal">{block.stage}</h3>
                  </div>

                  {/* Stage Items */}
                  <div className="space-y-4">
                    {block.items.map((item, itemIndex) => (
                      <motion.div
                        key={item.title}
                        initial={{ opacity: 1, x: -10 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: blockIndex * 0.15 + itemIndex * 0.1 }}
                        onMouseEnter={() => setHoveredCard(item.title)}
                        onMouseLeave={() => setHoveredCard(null)}
                        className={`bg-white rounded-xl p-5 shadow-sm border-2 transition-all duration-300 ${
                          hoveredCard === item.title
                            ? `${block.borderColor} shadow-lg`
                            : "border-transparent"
                        }`}
                      >
                        <span className={`inline-block px-2 py-1 text-xs font-serif font-medium tracking-widest rounded-full mb-2 ${block.tagColor}`}>
                          {item.tag}
                        </span>
                        <h4 className="font-serif font-light text-charcoal mb-2">{item.title}</h4>
                        <p className="text-charcoal/60 text-sm leading-relaxed">{item.desc}</p>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FINANCIAL SAFETY - ESCROW MODEL */}
<section className="py-24 bg-charcoal text-white overflow-hidden relative">

  {/* Ambient luxury lighting */}
  <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-[#D4A574]/10 blur-[140px] rounded-full" />
  <div className="absolute bottom-0 right-0 w-[500px] h-[400px] bg-[#4E342E]/20 blur-3xl rounded-full" />

  <div className="container mx-auto px-4 relative z-10">

    {/* Header */}
    <motion.div
      initial={{ opacity: 1, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8 }}
      className="text-center mb-24"
    >
      <span className="text-saddle-tan font-serif font-normal tracking-[0.25em] uppercase text-sm">
        {t('whyKRITIKAALPage.escrowBadge')}
      </span>

      <h2 className="text-5xl md:text-6xl leading-tight mt-6 font-light">
        {t('whyKRITIKAALPage.escrowTitle')}
      </h2>

      <h3 className="text-4xl md:text-5xl text-saddle-tan mt-5 font-medium">
        {t('whyKRITIKAALPage.escrowSubtitle')}
      </h3>
    </motion.div>

    {/* Steps Grid */}
    <div className="relative grid md:grid-cols-4 gap-14 mt-10">

      {/* Animated Curved Connector Line (more elegant stroke) */}
      <svg className="hidden md:block absolute top-28 left-0 w-full h-48 opacity-70" viewBox="0 0 1000 100" fill="none">
        <motion.path
          d="M0,60 C250,10 750,110 1000,60"
          stroke="url(#gradientLine)"
          strokeWidth="3"
          strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 1 }}
          whileInView={{ pathLength: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 2.2, ease: "easeInOut" }}
        />
        <defs>
          <linearGradient id="gradientLine" x1="0" y1="0" x2="1000" y2="0">
            <stop stopColor="#D4A574" />
            <stop offset="0.5" stopColor="#F5E6D3" />
            <stop offset="1" stopColor="#2C1810" />
          </linearGradient>
        </defs>
      </svg>

      {steps.map((step, i) => (
        <motion.div
          key={step.title}
          initial={{ opacity: 1, y: 60, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.2, duration: 0.7, ease: "easeOut" }}
          whileHover={{ y: -12, rotate: 0.5 }}
          className="group relative bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/10 hover:border-[#D4A574]/60 transition-all duration-500 shadow-lg hover:shadow-[0_20px_60px_rgba(0,0,0,0.5)]"
        >
          {/* Glow halo behind icon */}
          <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-28 h-28 bg-[#D4A574]/20 blur-2xl rounded-full opacity-0 group-hover:opacity-100 transition duration-500" />

          {/* Floating Icon */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            whileInView={{ scale: 1, rotate: 0 }}
            transition={{ delay: i * 0.2 + 0.3, type: "spring", stiffness: 120 }}
            className="absolute -top-14 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="w-24 h-24 rounded-full flex items-center justify-center border-4 shadow-2xl"
              style={{
                background: `radial-gradient(circle at 30% 30%, ${step.color}, #00000055)`,
                borderColor: step.borderColor,
              }}
            >
              <step.icon
                size={36}
                style={{
                  color: step.color === "#F5E6D3" ? "#2C1810" : "#F5E6D3",
                }}
              />
            </motion.div>
          </motion.div>

          <div className="mt-20 text-center">
            <h4 className="font-serif font-light text-lg text-[#D4A574] mb-3 tracking-wide">
              {step.title}
            </h4>
            <p className="text-[#F5E6D3]/80 text-sm leading-relaxed">
              {step.desc}
            </p>
          </div>
        </motion.div>
      ))}
    </div>

    {/* Bottom Protection Banner */}
    <motion.div
      initial={{ opacity: 1, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.4, duration: 0.8 }}
      className="mt-32 relative bg-gradient-to-r from-[#4E342E]/80 to-[#2C1810]/80 border border-[#D4A574]/40 rounded-3xl p-12 flex flex-col md:flex-row items-center justify-between gap-8 shadow-[0_0_60px_rgba(212,165,116,0.25)] overflow-hidden"
    >
      {/* Soft moving light sweep */}
      <motion.div
        animate={{ x: ["-100%", "100%"] }}
        transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        className="absolute top-0 left-0 w-1/2 h-full bg-gradient-to-r from-transparent via-white/10 to-transparent blur-2xl"
      />

      <div className="flex items-center gap-6 relative z-10">
        <motion.div
          animate={{ y: [0, -8, 0] }}
          transition={{ duration: 3, repeat: Infinity }}
          className="w-16 h-16 rounded-full bg-[#D4A574] flex items-center justify-center text-[#2C1810] text-2xl shadow-lg"
        >
          🛡️
        </motion.div>
        <div>
          <h4 className="font-serif font-light text-xl">{t('whyKRITIKAALPage.escrowFooterTitle')}</h4>
          <p className="text-[#F5E6D3]/80 text-sm">
            {t('whyKRITIKAALPage.escrowFooterDesc')}
          </p>
        </div>
      </div>

      <div className="relative z-10 bg-[#D4A574] text-[#2C1810] px-10 py-4 rounded-full font-serif font-normal shadow-xl hover:scale-105 transition-transform duration-300">
        {t('whyKRITIKAALPage.escrowFooterBadge')}
      </div>
    </motion.div>
  </div>
</section>


      {/* FIT CRITERIA */}
<section className="py-24 bg-warm-beige">
  <div className="container mx-auto px-4">
    <motion.h2
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="text-4xl md:text-5xl text-warm-beige text-center mb-16"
    >
      <span className="text-saddle-tan">{t('whyKRITIKAALPage.fitTitle')}</span>
    </motion.h2>

    <div className="grid lg:grid-cols-2 gap-12 max-w-5xl mx-auto">
      {/* ✅ THIS IS A FIT */}
<motion.div
  initial={{ opacity: 1, x: -30 }}
  whileInView={{ opacity: 1, x: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.6 }}
  whileHover={{ y: -5 }}
  className="bg-white rounded-3xl p-10 border border-[#D4A574]/30 shadow-[0_10px_40px_rgba(44,24,16,0.08)]"
>
  <div className="flex items-center gap-3 mb-6">
    <div className="w-12 h-12 rounded-xl bg-[#D4A574]/15 flex items-center justify-center">
      <Check className="w-6 h-6 text-[#4E342E]" />
    </div>
    <h3 className="text-2xl text-[#2C1810]">
      <span className="text-[#D4A574]">{t('whyKRITIKAALPage.fitIfTitle')}</span>
    </h3>
  </div>

  <ul className="space-y-4">
    {[
      t('whyKRITIKAALPage.fitIf1'),
      t('whyKRITIKAALPage.fitIf2'),
      t('whyKRITIKAALPage.fitIf3'),
      t('whyKRITIKAALPage.fitIf4'),
    ].map((item, index) => (
      <motion.li
        key={item}
        initial={{ opacity: 1, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1, duration: 0.5 }}
        viewport={{ once: true }}
        whileHover={{ x: 5 }}
        className="flex items-start gap-3 text-[#4E342E]/80"
      >
        <Check className="w-5 h-5 text-[#D4A574] shrink-0 mt-0.5" />
        {item}
      </motion.li>
    ))}
  </ul>
</motion.div>

{/* ❌ THIS IS NOT A FIT */}
<motion.div
  initial={{ opacity: 1, x: 30 }}
  whileInView={{ opacity: 1, x: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.6 }}
  whileHover={{ y: -5 }}
  className="bg-white rounded-3xl p-10 border border-[#D4A574]/30 shadow-[0_10px_40px_rgba(44,24,16,0.08)]"
>
  <div className="flex items-center gap-3 mb-6">
    <div className="w-12 h-12 rounded-xl bg-[#4E342E]/10 flex items-center justify-center">
      <X className="w-6 h-6 text-[#4E342E]" />
    </div>
    <h3 className="text-2xl text-[#2C1810]">
      <span className="text-[#D4A574]">{t('whyKRITIKAALPage.notFitTitle')}</span>
    </h3>
  </div>

  <ul className="space-y-4">
    {[
      t('whyKRITIKAALPage.notFit1'),
      t('whyKRITIKAALPage.notFit2'),
      t('whyKRITIKAALPage.notFit3'),
      t('whyKRITIKAALPage.notFit4'),
    ].map((item, index) => (
      <motion.li
        key={item}
        initial={{ opacity: 1, x: 20 }}
        whileInView={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1, duration: 0.5 }}
        viewport={{ once: true }}
        whileHover={{ x: -5 }}
        className="flex items-start gap-3 text-[#4E342E]/70"
      >
        <X className="w-5 h-5 text-[#4E342E] shrink-0 mt-0.5" />
        {item}
      </motion.li>
    ))}
  </ul>
</motion.div>

    </div>
  </div>
</section>

{/* WHAT WE DON'T MAKE  */}
<section className="pt-24 pb-24 bg-charcoal">
  <div className="container mx-auto px-4 max-w-6xl">

    <motion.div
      initial={{ opacity: 1, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.3 }}
      className="mt-12 bg-gradient-to-br from-[#2C1810] to-[#1A0F0A] border border-[#D4A574]/30 rounded-3xl p-8 md:p-12 shadow-[0_25px_80px_rgba(0,0,0,0.6)]"
    >
      {/* Header */}
      <div className="flex items-center justify-center gap-3 mb-10">
        <X className="w-6 h-6 text-[#D4A574]" />
        <h3 className="text-[#F5E6D3] font-serif font-light text-xl tracking-wide">
          <span className="text-[#D4A574]">{t('whyKRITIKAALPage.notManufactured')}:</span>
        </h3>
      </div>

      {/* Items */}
      <div className="grid md:grid-cols-3 gap-6">
        {notManufactured.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 * index }}
            whileHover={{ y: -4 }}
            className="flex items-center gap-4 p-5 bg-[#F5E6D3]/5 rounded-xl border border-[#D4A574]/20 hover:border-[#D4A574]/40 transition-all duration-300"
          >
            <item.icon className="w-6 h-6 text-[#D4A574]" />
            <span className="text-[#F5E6D3]/80 text-sm md:text-base">
              {item.item}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  </div>
</section>

      {/* CTA */}
<section className="relative py-24 overflow-hidden">
  <div className="absolute inset-0 z-0">
    <img
      src="/leather-bg.jpg"
      alt="Leather craftsmanship"
      className="w-full h-full object-cover"
    />
    <div className="absolute inset-0 bg-charcoal/90" />
  </div>

  <div className="container mx-auto px-4 relative z-10">
    <motion.div
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="max-w-2xl mx-auto text-center"
    >
      <h2 className=" text-4xl text-warm-beige mb-6">
        {t('whyKRITIKAALPage.ctaTitle')}{" "}
        <span className="text-saddle-tan">{t('whyKRITIKAALPage.ctaTitleHighlight')}</span>{t('whyKRITIKAALPage.ctaTitleEnd')}
      </h2>

      <p className="text-warm-beige/80 mb-8">
        {t('whyKRITIKAALPage.ctaSubtitle')}
      </p>

      <Link href="/bookacall">
        <div className="leather-stitch-box inline-block">
          <Button
            className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal"
            size="lg"
          >
            {t('whyKRITIKAALPage.ctaButton')}
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </Link>
    </motion.div>
  </div>
</section>


    </>
  );
};

export default WhyKRITIKAAL;
