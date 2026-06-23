"use client";

import { motion, AnimatePresence, useMotionValue, useSpring } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, TrendingUp, Award, MapPin, Factory, Leaf, UserCheck, Shield, DollarSign, Clock, CheckCircle, Check, Truck, Users, Globe, ShieldCheck, TrendingDown, X, Building2, Scissors, Ship, TreePine, ShoppingBag, Sparkles, Target, Zap } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";
import dynamic from "next/dynamic";

const ChinaSatelliteMap = dynamic(() => import("@/components/home/ChinaSatelliteMap"), { ssr: false, loading: () => <div className="w-full h-full animate-pulse bg-charcoal/20 rounded-2xl" /> });
const IndiaSatelliteMap = dynamic(() => import("@/components/home/IndiaSatelliteMap"), { ssr: false, loading: () => <div className="w-full h-full animate-pulse bg-charcoal/20 rounded-2xl" /> });

/* ANIMATED NUMBER COMPONENT */
const AnimatedNumber = ({ value, prefix = "", suffix = "" }: { value: number; prefix?: string; suffix?: string }) => {
  const [displayValue, setDisplayValue] = useState(0);
  
  useEffect(() => {
    const duration = 800;
    const steps = 30;
    const increment = value / steps;
    let current = 0;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setDisplayValue(value);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, duration / steps);
    
    return () => clearInterval(timer);
  }, [value]);
  
  return (
    <span className="tabular-nums">
      {prefix}{displayValue.toLocaleString("en-GB", { maximumFractionDigits: 0 })}{suffix}
    </span>
  );
};

/* LUXURY BACKGROUND COMPONENT */
const LuxuryBackground = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 50, damping: 20 });
  
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };
  
  return (
    <div className={`relative ${className}`} onMouseMove={handleMouseMove}>
      {/* Noise texture overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none z-0"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
      {/* Radial glow following mouse */}
      <motion.div
        className="absolute w-[600px] h-[600px] rounded-full pointer-events-none z-0 opacity-20"
        style={{
          background: "radial-gradient(circle, rgba(245,230,211,0.15) 0%, transparent 70%)",
          x: springX,
          y: springY,
          translateX: "-50%",
          translateY: "-50%",
        }}
      />
      {children}
    </div>
  );
};

/* STAGGER CONTAINER FOR ANIMATIONS */
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.1, 0.25, 1] as const }
  },
};


/* DATA */

const getLeatherHeritage = (t: any) => [
  {
    region: t('whyIndiaPage.heritageTamilNadu'),
    specialty: t('whyIndiaPage.heritageTNSpecialty'),
    icon: MapPin,
  },
  {
    region: t('whyIndiaPage.heritageUttarPradesh'),
    specialty: t('whyIndiaPage.heritageUPSpecialty'),
    icon: MapPin,
  },
  {
    region: t('whyIndiaPage.heritageWestBengal'),
    specialty: t('whyIndiaPage.heritageWBSpecialty'),
    icon: MapPin,
  },
  {
    region: t('whyIndiaPage.heritageKarnataka'),
    specialty: t('whyIndiaPage.heritageKASpecialty'),
    icon: MapPin,
  },
];

const globalShift = [
  {
    title: "30% Lower FOB Costs",
    description:
      "Indiaâ€™s skilled leather manufacturing delivers major cost savings as Chinaâ€™s wages continue rising.",
    icon: TrendingDown,
  },
  {
    title: "Abundant Skilled Workforce",
    description:
      "Access to the worldâ€™s largest artisan leather workforce ensures stable production capacity.",
    icon: Users,
  },
  {
    title: "0% UK Import Duty",
    description:
      "Free Trade Agreements give Indian leather goods duty-free access to key global markets.",
    icon: Globe,
  },
  {
    title: "Higher Margins, Lower Risk",
    description:
      "Avoid tariff barriers and cost erosion faced by China-based sourcing.",
    icon: ShieldCheck,
  },
];

const whyNow = [
  {
    icon: Clock,
    title: "Perfect Timing",
    description: "As global supply chains restructure, India is positioned as the preferred alternative for leather manufacturing.",
  },
  {
    icon: TrendingUp,
    title: "Growing Infrastructure",
    description: "Massive investments in ports, logistics, and manufacturing zones are making exports faster and more efficient.",
  },
  {
    icon: CheckCircle,
    title: "Quality Standards",
    description: "Indian manufacturers now meet international quality standards (ISO, REACH, BSCI) required by global brands.",
  },
];

/* PAGE */

const WhyIndia = () => {
  const { t } = useTranslation();
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);
  
  const data = [
    {
      icon: DollarSign,
      title: t('whyIndiaPage.comparisonTitle1'),
      china: {
        main: t('whyIndiaPage.comparisonChinaMain1'),
        sub: t('whyIndiaPage.comparisonChinaSub1'),
        color: "text-red-400",
      },
      india: {
        main: t('whyIndiaPage.comparisonIndiaMain1'),
        tag: t('whyIndiaPage.comparisonIndiaTag1'),
        sub: t('whyIndiaPage.comparisonIndiaSub1'),
        color: "text-saddle-tan-400",
      },
    },
    {
      icon: Users,
      title: t('whyIndiaPage.comparisonTitle2'),
      china: {
        main: t('whyIndiaPage.comparisonChinaMain2'),
        sub: t('whyIndiaPage.comparisonChinaSub2'),
        color: "text-red-400",
      },
      india: {
        main: t('whyIndiaPage.comparisonIndiaMain2'),
        tag: t('whyIndiaPage.comparisonIndiaTag2'),
        sub: "",
        color: "text-amber-400",
      },
    },
    {
      icon: Truck,
      title: t('whyIndiaPage.comparisonTitle3'),
      china: {
        main: t('whyIndiaPage.comparisonChinaMain3'),
        sub: t('whyIndiaPage.comparisonChinaSub3'),
        color: "text-red-400",
      },
      india: {
        main: t('whyIndiaPage.comparisonIndiaMain3'),
        tag: t('whyIndiaPage.comparisonIndiaTag3'),
        sub: "",
        color: "text-amber-400",
      },
    },
  ];
  
  const indiaAdvantages = [
    {
      icon: DollarSign,
      title: t('whyIndiaPage.advantage1'),
      description: t('whyIndiaPage.advantage1Desc'),
      stats: t('whyIndiaPage.advantage1Stats'),
    },
    {
      icon: Users,
      title: t('whyIndiaPage.advantage2'),
      description: t('whyIndiaPage.advantage2Desc'),
      stats: t('whyIndiaPage.advantage2Stats'),
    },
    {
      icon: Factory,
      title: t('whyIndiaPage.advantage3'),
      description: t('whyIndiaPage.advantage3Desc'),
      stats: t('whyIndiaPage.advantage3Stats'),
    },
    {
      icon: Globe,
      title: t('whyIndiaPage.advantage4'),
      description: t('whyIndiaPage.advantage4Desc'),
      stats: t('whyIndiaPage.advantage4Stats'),
    },
  ];

  return (
    <>
     {/* Hero Section - Before & After Corona Comparison */}
      <section className="relative pt-24 pb-24 overflow-hidden">

  {/* Premium navy gradient background */}
  <div className="absolute inset-0">
          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
          <div className="absolute inset-0 bg-charcoal/85" />
        </div>

  {/* Animated Globe Background */}
  <motion.div
    animate={{ rotate: 360 }}
    transition={{ duration: 200, repeat: Infinity, ease: "linear" }}
    className="absolute inset-0 opacity-5"
  >
    <svg className="w-full h-full" viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
      <circle cx="400" cy="300" r="200" stroke="#F5E6D3" strokeWidth="0.5" fill="none" opacity="0.3" />
      <ellipse cx="400" cy="300" rx="200" ry="80" stroke="#F5E6D3" strokeWidth="0.5" fill="none" opacity="0.3" />
      <ellipse cx="400" cy="300" rx="80" ry="200" stroke="#F5E6D3" strokeWidth="0.5" fill="none" opacity="0.3" />
      <line x1="200" y1="300" x2="600" y2="300" stroke="#F5E6D3" strokeWidth="0.5" opacity="0.3" />
    </svg>
  </motion.div>

  <div className="container mx-auto px-4 md:px-6 lg:px-8 relative z-10">

    {/* Section Title - Centered with better spacing */}
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
        {t('whyIndiaPage.badge')}
      </motion.span>
       <motion.h1
                className="text-4xl md:text-5xl lg:text-6xl text-warm-beige mb-6 leading-tight"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
        {t('whyIndiaPage.heroTitle')} <span className="text-saddle-tan">{t('whyIndiaPage.heroTitleHighlight')}</span>
      </motion.h1>
      <motion.p
                className="text-xl text-warm-beige/80 leading-relaxed mb-10"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
        {t('whyIndiaPage.heroSubtitle')}
      </motion.p>
    </motion.div>

    <div className="grid lg:grid-cols-2 gap-16 lg:gap-24 max-w-7xl mx-auto relative mt-8 md:mt-12 lg:mt-16">

      {/* LEFT PANEL - Before Corona */}
      <motion.div 
        initial={{ opacity: 1, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative group"
      >
        {/* Premium ambient red glow behind card */}
        <div className="absolute -inset-4 bg-gradient-radial from-red-500/20 via-red-500/5 to-transparent rounded-3xl blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
        
        {/* Glassmorphism card with enhanced effects */}
        <div className="relative backdrop-blur-xl bg-slate-900/40 border border-red-500/20 rounded-2xl p-8 shadow-2xl hover:shadow-red-500/20 transition-all duration-500 hover:border-red-500/40">
          
          {/* Header section with improved spacing */}
          <div className="mb-10 space-y-5">
            <motion.span 
              className="inline-block px-5 py-2 bg-red-500/15 border border-red-500/40 rounded-full text-red-400 text-sm font-serif font-medium tracking-wide backdrop-blur-sm"
              whileHover={{ scale: 1.05 }}
            >
              {t('whyIndiaPage.beforeBadge')}
            </motion.span>
            
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-serif font-medium mb-4 leading-tight tracking-wide">
              <span className="text-red-400 drop-shadow-lg">{t('whyIndiaPage.beforeTitle')}</span>
            </h2>
            
            <p className="text-warm-beige/80 text-lg leading-relaxed font-serif font-normal">
              {t('whyIndiaPage.beforeSubtitle')}
            </p>
          </div>

          {/* Map Container with improved spacing */}
          <div className="relative">
            <motion.div
              initial={{ opacity: 1, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              whileHover={{ scale: 1.02 }}
              className="relative w-full aspect-[4/3] z-10"
            >
              {/* Interactive China Satellite Map with premium border */}
              <div className="w-full h-full rounded-2xl overflow-hidden bg-gradient-to-br from-blue-900 via-blue-950 to-slate-950 border border-red-500/30 shadow-2xl shadow-red-500/20 hover:shadow-red-500/40 transition-shadow duration-500">
                <ChinaSatelliteMap />
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* RIGHT PANEL - After Corona */}
      <motion.div 
        initial={{ opacity: 1, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
        className="relative group"
      >
        {/* Premium ambient green glow behind card */}
        <div className="absolute -inset-4 bg-gradient-radial from-green-500/20 via-green-500/5 to-transparent rounded-3xl blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
        
        {/* Glassmorphism card with enhanced effects */}
        <div className="relative backdrop-blur-xl bg-slate-900/40 border border-green-500/20 rounded-2xl p-8 shadow-2xl hover:shadow-green-500/20 transition-all duration-500 hover:border-green-500/40">
          
          {/* Header section with improved spacing */}
          <div className="mb-10 space-y-5">
            <motion.span 
              className="inline-block px-5 py-2 bg-green-500/15 border border-green-500/40 rounded-full text-green-400 text-sm font-serif font-medium tracking-wide backdrop-blur-sm"
              whileHover={{ scale: 1.05 }}
            >
              {t('whyIndiaPage.afterBadge')}
            </motion.span>
            
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-serif font-medium mb-4 leading-tight tracking-wide">
              <span className="text-green-400 drop-shadow-lg">{t('whyIndiaPage.afterTitle')}</span>
            </h2>
            
            <p className="text-warm-beige/80 text-lg leading-relaxed font-serif font-normal">
              {t('whyIndiaPage.afterSubtitle')}
            </p>
          </div>

          {/* Map Container with improved spacing */}
          <div className="relative">
            <motion.div
              initial={{ opacity: 1, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
              whileHover={{ scale: 1.02 }}
              className="relative w-full aspect-[4/3] z-10"
            >
              {/* Interactive India Satellite Map with premium border */}
              <div className="w-full h-full rounded-2xl overflow-hidden bg-gradient-to-br from-blue-900 via-blue-950 to-slate-950 border border-green-500/30 shadow-2xl shadow-green-500/20 hover:shadow-green-500/40 transition-shadow duration-500">
                <IndiaSatelliteMap />
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
    </div>

    {/* Bottom Summary with enhanced styling */}
    <motion.div 
      className="mt-20 text-center max-w-4xl mx-auto"
      initial={{ opacity: 1, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, delay: 0.3 }}
    >
      <div className="backdrop-blur-sm bg-slate-900/30 border border-warm-beige/10 rounded-2xl p-8 md:p-10">
        <p className="text-warm-beige/90 text-xl md:text-2xl leading-relaxed font-serif font-light">
          {t('whyIndiaPage.heroSummaryPart1')}
          {' '}
          <span className="text-saddle-tan font-serif font-light">{t('whyIndiaPage.heroSummaryHighlight')}</span>
          {' '}
          {t('whyIndiaPage.heroSummaryPart2')}
        </p>
      </div>
    </motion.div>
  </div>
</section>

      {/* Geopolitical Comparison Section */}
<section className="py-24 md:py-24 bg-warm-beige relative overflow-hidden">
  {/* Subtle radial gradient */}
  <div className="absolute inset-0 opacity-30 pointer-events-none">
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-radial from-[#D4A574]/20 to-transparent rounded-full blur-3xl" />
  </div>
  
  <div className="container mx-auto px-4 sm:px-6 md:px-10 lg:px-16 relative z-10">

    {/* Header */}
    <motion.div
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="text-center mb-10 md:mb-16"
    >
      <span className="text-saddle-tan font-serif font-medium tracking-widest uppercase text-xs sm:text-sm">
        {t('whyIndiaPage.geopoliticalBadge')}
      </span>

      <h2 className="text-3xl sm:text-4xl md:text-5xl text-charcoal mt-4 mb-4 font-serif font-medium">
        {t('whyIndiaPage.geopoliticalTitleChina')}
      </h2>

      <h3 className="text-2xl sm:text-3xl md:text-4xl text-saddle-tan font-serif font-normal">
        {t('whyIndiaPage.geopoliticalTitleIndia')}
      </h3>

      <p className="text-charcoal/70 mt-6 max-w-3xl mx-auto text-sm sm:text-base font-serif font-normal">
        {t('whyIndiaPage.geopoliticalSubtitle')}
      </p>
    </motion.div>

    {/* Comparison Grid */}
    <motion.div 
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-10 max-w-6xl mx-auto"
    >

      {/* LEFT â€” Instability */}
      <motion.div
        variants={staggerItem}
        whileHover={{ y: -4, boxShadow: "0 20px 40px rgba(44,24,16,0.1)" }}
        className="bg-white rounded-2xl p-6 sm:p-8 md:p-10 shadow-sm border border-charcoal/10 hover:border-saddle-tan/30 transition-all duration-300"
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 md:mb-8">
  <h3 className="flex items-center gap-2 text-xl sm:text-2xl text-charcoal">
    <img
      src="https://flagcdn.com/w40/cn.png"
      alt="China Flag"
      className="w-6 h-4 object-cover rounded-sm"
    />
    {t('whyIndiaPage.instabilityTitle')}
  </h3>

  <span className="px-4 py-1 text-xs sm:text-sm rounded-full bg-charcoal/10 text-red-600 font-serif font-medium">
    {t('whyIndiaPage.instabilityRisk')}
  </span>
</div>
        {/* Item 1 */}
        <div className="mb-5 md:mb-6">
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.instabilityPoliticalLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.instabilityPoliticalTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.instabilityPoliticalDesc')}</p>
        </div>

        {/* Item 2 */}
        <div className="mb-5 md:mb-6">
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.instabilityWorkforceLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.instabilityWorkforceTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.instabilityWorkforceDesc')}</p>
        </div>

        {/* Item 3 */}
        <div>
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.instabilityEconomicLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.instabilityEconomicTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.instabilityEconomicDesc')}</p>
        </div>
      </motion.div>

      {/* RIGHT â€” Stability */}
      <motion.div
        variants={staggerItem}
        whileHover={{ y: -4, boxShadow: "0 20px 40px rgba(212,165,116,0.15)" }}
        className="bg-white rounded-2xl p-6 sm:p-8 md:p-10 shadow-sm border border-charcoal/10 hover:border-saddle-tan/50 transition-all duration-300"
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 md:mb-8">
  <h3 className="flex items-center gap-2 text-xl sm:text-2xl text-charcoal">
    <img
      src="https://flagcdn.com/w40/in.png"
      alt="India Flag"
      className="w-6 h-4 object-cover rounded-sm"
    />
    {t('whyIndiaPage.stabilityTitle')}
  </h3>

  <span className="px-4 py-1 text-xs sm:text-sm rounded-full bg-charcoal/10 text-green-600 font-serif font-medium">
    {t('whyIndiaPage.stabilityRisk')}
  </span>
</div>


        {/* Item 1 */}
        <div className="mb-5 md:mb-6">
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.stabilityPoliticalLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.stabilityPoliticalTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.stabilityPoliticalDesc')}</p>
        </div>

        {/* Item 2 */}
        <div className="mb-5 md:mb-6">
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.stabilityWorkforceLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.stabilityWorkforceTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.stabilityWorkforceDesc')}</p>
        </div>

        {/* Item 3 */}
        <div>
          <p className="text-saddle-tan font-serif font-medium text-xs sm:text-sm uppercase">{t('whyIndiaPage.stabilityEconomicLabel')}</p>
          <p className="text-lg sm:text-xl text-charcoal mt-1 font-serif font-normal">{t('whyIndiaPage.stabilityEconomicTitle')}</p>
          <p className="text-charcoal/70 text-xs sm:text-sm mt-1 font-serif font-light">{t('whyIndiaPage.stabilityEconomicDesc')}</p>
        </div>
      </motion.div>
    </motion.div>

    {/* Bottom Statement */}
    <motion.div
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.2 }}
      className="mt-10 md:mt-16 text-center"
    >
      <motion.div 
        whileHover={{ scale: 1.02 }}
        className="inline-block bg-saddle-tan text-white font-serif font-medium px-6 sm:px-8 py-3 sm:py-4 rounded-full shadow-md text-sm sm:text-base"
      >
        {t('whyIndiaPage.geopoliticalFooter')}
      </motion.div>
    </motion.div>

  </div>
</section>




      {/* India Powerhouse â€” Strategic Ecosystem */}
<section className="py-24 md:py-24 bg-charcoal relative overflow-hidden">
      {/* Noise texture */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 lg:px-16 relative z-10">

        {/* Heading */}
        <motion.div 
  initial={{ opacity: 1, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  className="mb-12 md:mb-20 max-w-3xl mx-auto text-center"
>
  <p className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
    {t('whyIndiaPage.powerhouseBadge')}
  </p>

  <h2 className="text-4xl sm:text-5xl md:text-6xl  leading-tight text-white">
    {t('whyIndiaPage.powerhouseTitle')} <span className="text-saddle-tan">{t('whyIndiaPage.powerhouseTitleHighlight')}</span> {t('whyIndiaPage.powerhouseTitleEnd')}
  </h2>

  <p className="text-[#F5E6D3]/60 mt-6 text-base sm:text-lg">
    {t('whyIndiaPage.powerhouseSubtitle')}
  </p>
</motion.div>

        {/* Mobile Cards View */}
        <div className="lg:hidden space-y-4">
          {[
            { icon: Building2, title: t('whyIndiaPage.powerhouseGovSupportTitle'), desc: t('whyIndiaPage.powerhouseGovSupportDesc'), stat: t('whyIndiaPage.powerhouseGovSupportStat'), color: "text-white" },
            { icon: Scissors, title: t('whyIndiaPage.powerhouseArtisansTitle'), desc: t('whyIndiaPage.powerhouseArtisansDesc'), stat: t('whyIndiaPage.powerhouseArtisansStat'), color: "text-white" },
            { icon: Ship, title: t('whyIndiaPage.powerhouseLogisticsTitle'), desc: t('whyIndiaPage.powerhouseLogisticsDesc'), stat: t('whyIndiaPage.powerhouseLogisticsStat'), color: "text-white" },
            { icon: TreePine, title: t('whyIndiaPage.powerhouseRawTitle'), desc: t('whyIndiaPage.powerhouseRawDesc'), stat: t('whyIndiaPage.powerhouseRawStat'), color: "text-white" },
            { icon: ShoppingBag, title: t('whyIndiaPage.powerhouseDomesticTitle'), desc: t('whyIndiaPage.powerhouseDomesticDesc'), stat: t('whyIndiaPage.powerhouseDomesticStat'), color: "text-white" },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 1, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -6 }}
              className="bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-3xl p-6 shadow-[0_8px_24px_rgba(0,0,0,0.3),_0_0_15px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 hover:shadow-[0_12px_32px_rgba(212,165,116,0.2)] transition-all duration-300 overflow-hidden group"
            >
              {/* Gradient overlay on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              <div className="relative z-10">
                <div className="flex items-start gap-4 mb-3">
                  <motion.div
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="w-12 h-12 rounded-xl bg-[#D4A574]/20 border border-[#D4A574]/40 flex items-center justify-center flex-shrink-0"
                  >
                    <item.icon className="w-6 h-6 text-[#D4A574]" />
                  </motion.div>
                  <div className="flex-1">
                    <h3 className={`${item.color} font-serif font-light text-lg mb-2`}>{item.title}</h3>
                  </div>
                </div>
                <p className="text-[#F5E6D3]/70 text-sm mb-3 leading-relaxed">{item.desc}</p>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#D4A574]" />
                  <p className="text-white text-sm font-serif font-normal">{item.stat}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

       {/* Desktop Diagram Area */}
<div className="hidden lg:flex relative items-center justify-center h-[720px]">

  {/* Outer Ring */}
  <div className="absolute w-[760px] h-[760px] rounded-full border border-[#F5E6D3]/5" />

  {/* Center Hub */}
  <motion.div
    initial={{ scale: 0.8, opacity: 1 }}
    whileInView={{ scale: 1, opacity: 1 }}
    transition={{ duration: 0.7 }}
    className="relative z-20 w-64 h-64 rounded-full border-4 border-[#D4A574] flex flex-col items-center justify-center bg-[#2C1810] shadow-[0_0_90px_rgba(212,165,116,0.35)]"
  >
    {/* Pulsing rings */}
    <motion.div
      animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.2, 0.5] }}
      transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      className="absolute inset-0 rounded-full border-2 border-[#D4A574]/30"
    />
    <motion.div
      animate={{ scale: [1, 1.25, 1], opacity: [0.3, 0.1, 0.3] }}
      transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      className="absolute inset-0 rounded-full border border-[#D4A574]/20"
    />
    
    <motion.img
      animate={{ y: [0, -5, 0] }}
      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      src="https://flagcdn.com/w80/in.png"
      alt="India Flag"
      className="w-16 mb-3 relative z-10"
    />
    <p className="text-[#D4A574] font-serif font-medium tracking-widest text-lg relative z-10">{t('whyIndiaPage.powerhouseTitleHighlight').toUpperCase()}</p>
    <p className="text-[#F5E6D3]/60 text-sm tracking-wider relative z-10">{t('whyIndiaPage.powerhouseMfgHub')}</p>
  </motion.div>

  

  {/* Top Center â€” Government Support */}
  <motion.div
    initial={{ opacity: 1, y: -30 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.2, duration: 0.5 }}
    whileHover={{ 
      y: -8, 
      boxShadow: "0 25px 50px rgba(212,165,116,0.25), 0 0 40px rgba(212,165,116,0.15)",
      borderColor: "rgba(212,165,116,0.7)",
    }}
    className="absolute top-0 bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-2xl p-5 w-[280px] text-center shadow-[0_8px_32px_rgba(0,0,0,0.3),_0_0_20px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 transition-all duration-300 cursor-pointer group overflow-hidden"
  >
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    
    <div className="relative z-10">
      <motion.div
        whileHover={{ scale: 1.1, rotate: 5 }}
        className="w-12 h-12 rounded-full bg-[#D4A574]/20 border-2 border-[#D4A574] flex items-center justify-center mx-auto mb-3"
      >
        <Building2 className="w-6 h-6 text-[#D4A574]" />
      </motion.div>
      <h3 className="text-saddle-tan font-serif font-light text-base mb-2">
        {t('whyIndiaPage.powerhouseGovSupportTitle')}
      </h3>
      <p className="text-[#F5E6D3]/70 text-xs mb-3 leading-relaxed">
        {t('whyIndiaPage.powerhouseGovSupportDesc')}
      </p>
      <div className="inline-flex items-center gap-2 bg-[#D4A574]/20 px-2.5 py-1 rounded-full">
        <Zap className="w-3.5 h-3.5 text-[#D4A574]" />
        <p className="text-white text-xs font-serif font-normal">{t('whyIndiaPage.powerhouseGovSupportStat')}</p>
      </div>
    </div>
  </motion.div>

  {/* Top Left â€” Skilled Artisans */}
  <motion.div
    initial={{ opacity: 1, x: -30 }}
    whileInView={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.25, duration: 0.5 }}
    whileHover={{ 
      x: -8, 
      boxShadow: "0 25px 50px rgba(212,165,116,0.25), 0 0 40px rgba(212,165,116,0.15)",
      borderColor: "rgba(212,165,116,0.7)",
    }}
    className="absolute left-[3%] top-[22%] bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-2xl p-5 w-[240px] shadow-[0_8px_32px_rgba(0,0,0,0.3),_0_0_20px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 transition-all duration-300 cursor-pointer group overflow-hidden"
  >
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    
    <div className="relative z-10">
      <motion.div
        whileHover={{ scale: 1.1, rotate: -5 }}
        className="w-10 h-10 rounded-xl bg-[#D4A574]/20 border border-[#D4A574] flex items-center justify-center mb-3"
      >
        <Scissors className="w-5 h-5 text-[#D4A574]" />
      </motion.div>
      <h3 className="text-saddle-tan font-serif font-light text-base mb-2">
        {t('whyIndiaPage.powerhouseArtisansTitle')}
      </h3>
      <p className="text-[#F5E6D3]/70 text-xs mb-3 leading-relaxed">
        {t('whyIndiaPage.powerhouseArtisansDesc')}
      </p>
      <div className="inline-flex items-center gap-2 bg-[#D4A574]/20 px-2.5 py-1 rounded-full">
        <Target className="w-3.5 h-3.5 text-[#D4A574]" />
        <p className="text-white text-xs font-serif font-normal">{t('whyIndiaPage.powerhouseArtisansStat')}</p>
      </div>
    </div>
  </motion.div>

  {/* Top Right â€” Logistics Advantage */}
  <motion.div
    initial={{ opacity: 1, x: 30 }}
    whileInView={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.25, duration: 0.5 }}
    whileHover={{ 
      x: 8, 
      boxShadow: "0 25px 50px rgba(212,165,116,0.25), 0 0 40px rgba(212,165,116,0.15)",
      borderColor: "rgba(212,165,116,0.7)",
    }}
    className="absolute right-[3%] top-[22%] bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-2xl p-5 w-[240px] shadow-[0_8px_32px_rgba(0,0,0,0.3),_0_0_20px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 transition-all duration-300 cursor-pointer group overflow-hidden"
  >
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    
    <div className="relative z-10">
      <motion.div
        whileHover={{ scale: 1.1, rotate: 5 }}
        className="w-10 h-10 rounded-xl bg-[#D4A574]/20 border border-[#D4A574] flex items-center justify-center mb-3"
      >
        <Ship className="w-5 h-5 text-[#D4A574]" />
      </motion.div>
      <h3 className="text-saddle-tan font-serif font-light text-base mb-2">
        {t('whyIndiaPage.powerhouseLogisticsTitle')}
      </h3>
      <p className="text-[#F5E6D3]/70 text-xs mb-3 leading-relaxed">
        {t('whyIndiaPage.powerhouseLogisticsDesc')}
      </p>
      <div className="inline-flex items-center gap-2 bg-[#D4A574]/20 px-2.5 py-1 rounded-full">
        <Truck className="w-3.5 h-3.5 text-[#D4A574]" />
        <p className="text-white text-xs font-serif font-normal">{t('whyIndiaPage.powerhouseLogisticsStat')}</p>
      </div>
    </div>
  </motion.div>

  {/* Bottom Left â€” Raw Materials */}
  <motion.div
    initial={{ opacity: 1, x: -30 }}
    whileInView={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.3, duration: 0.5 }}
    whileHover={{ 
      x: -8, 
      boxShadow: "0 25px 50px rgba(212,165,116,0.25), 0 0 40px rgba(212,165,116,0.15)",
      borderColor: "rgba(212,165,116,0.7)",
    }}
    className="absolute left-[10%] bottom-[12%] bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-2xl p-5 w-[250px] shadow-[0_8px_32px_rgba(0,0,0,0.3),_0_0_20px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 transition-all duration-300 cursor-pointer group overflow-hidden"
  >
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    
    <div className="relative z-10">
      <motion.div
        whileHover={{ scale: 1.1, rotate: -5 }}
        className="w-10 h-10 rounded-xl bg-[#D4A574]/20 border border-[#D4A574] flex items-center justify-center mb-3"
      >
        <TreePine className="w-5 h-5 text-[#D4A574]" />
      </motion.div>
      <h3 className="text-saddle-tan font-serif font-light text-base mb-2">
        {t('whyIndiaPage.powerhouseRawTitle')}
      </h3>
      <p className="text-[#F5E6D3]/70 text-xs mb-3 leading-relaxed">
        {t('whyIndiaPage.powerhouseRawDesc')}
      </p>
      <div className="inline-flex items-center gap-2 bg-[#D4A574]/20 px-2.5 py-1 rounded-full">
        <Leaf className="w-3.5 h-3.5 text-[#D4A574]" />
        <p className="text-white text-xs font-serif font-normal">{t('whyIndiaPage.powerhouseRawStat')}</p>
      </div>
    </div>
  </motion.div>

  {/* Bottom Right â€” Domestic Supply */}
  <motion.div
    initial={{ opacity: 1, x: 30 }}
    whileInView={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.3, duration: 0.5 }}
    whileHover={{ 
      x: 8, 
      boxShadow: "0 25px 50px rgba(212,165,116,0.25), 0 0 40px rgba(212,165,116,0.15)",
      borderColor: "rgba(212,165,116,0.7)",
    }}
    className="absolute right-[10%] bottom-[12%] bg-gradient-to-br from-[#5C4033]/90 via-[#4E342E]/85 to-[#3D2817]/80 backdrop-blur-xl border-2 border-[#F5E6D3]/15 rounded-2xl p-5 w-[250px] shadow-[0_8px_32px_rgba(0,0,0,0.3),_0_0_20px_rgba(212,165,116,0.1)] hover:border-[#D4A574]/50 transition-all duration-300 cursor-pointer group overflow-hidden"
  >
    {/* Gradient overlay on hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-[#D4A574]/0 to-[#D4A574]/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
    
    <div className="relative z-10">
      <motion.div
        whileHover={{ scale: 1.1, rotate: 5 }}
        className="w-10 h-10 rounded-xl bg-[#D4A574]/20 border border-[#D4A574] flex items-center justify-center mb-3"
      >
        <ShoppingBag className="w-5 h-5 text-[#D4A574]" />
      </motion.div>
      <h3 className="text-saddle-tan font-serif font-light text-base mb-2">
        {t('whyIndiaPage.powerhouseDomesticTitle')}
      </h3>
      <p className="text-[#F5E6D3]/70 text-xs mb-3 leading-relaxed">
        {t('whyIndiaPage.powerhouseDomesticDesc')}
      </p>
      <div className="inline-flex items-center gap-2 bg-[#D4A574]/20 px-2.5 py-1 rounded-full">
        <TrendingUp className="w-3.5 h-3.5 text-[#D4A574]" />
        <p className="text-white text-xs font-serif font-normal">{t('whyIndiaPage.powerhouseDomesticStat')}</p>
      </div>
    </div>
  </motion.div>

 
  {/* Bottom Tagline */}
  <p className="absolute bottom-6 text-[#F5E6D3]/40 tracking-widest text-sm">
    {t('whyIndiaPage.powerhouseTagline')}
  </p>
</div>
      </div>
    </section>

    {/* Managed Manufacturing VS Sourcing Agencies */}
<section className="relative py-24 md:py-32 overflow-hidden bg-[#F5E6D3]">

  {/* Ambient background accents */}
  <div className="absolute -top-40 -left-40 w-[520px] h-[520px] bg-[#D4A574]/10 rounded-full blur-3xl" />
  <div className="absolute -bottom-40 -right-40 w-[520px] h-[520px] bg-[#4E342E]/10 rounded-full blur-3xl" />

  <div className="container mx-auto px-4 relative z-10">

    {/* Heading */}
    <motion.div
      initial={{ opacity: 1, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.9 }}
      className="mb-14 md:mb-20 text-center"
    >
      <p className="text-saddle-tan font-serif font-normal tracking-[0.25em] uppercase text-xs sm:text-sm">
        {t('whyIndiaPage.managedVsAgentBadge')}
      </p>
      <h2 className="text-3xl sm:text-4xl md:text-5xl text-saddle-tan leading-tight mt-3">
        {t('whyIndiaPage.managedVsAgentTitle')} <span className="text-black">{t('whyIndiaPage.managedVsAgentTitleVS')}</span> {t('whyIndiaPage.managedVsAgentTitleEnd')}
      </h2>
      <p className="text-[#2C1810]/70 mt-4 text-sm sm:text-base">
        {t('whyIndiaPage.managedVsAgentSubtitle')}
      </p>
    </motion.div>

    <div className="grid lg:grid-cols-2 gap-12 max-w-6xl mx-auto">

      {/* LEFT CARD - Managed Manufacturing (Saddle Tan Theme) */}
      <motion.div
        initial={{ opacity: 1, x: -60 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        whileHover={{ y: -10 }}
        className="group relative bg-gradient-to-br from-[#E6C7A8]/95 via-[#D8B08C]/95 to-[#EAD3B7]/95 backdrop-blur-xl rounded-3xl p-10 shadow-xl border-2 border-[#C19A78] hover:shadow-2xl hover:shadow-[#B08968]/30 transition-all duration-500"
      >
        {/* Side Accent Bar */}
        <div className="absolute left-0 top-10 bottom-10 w-2 rounded-full bg-gradient-to-b from-[#B08968] via-[#C19A78] to-[#D8B08C] shadow-lg shadow-[#B08968]/40" />

        <h3 className="text-2xl text-[#6F4E37] mb-8 pl-6 font-serif font-medium">
          {t('whyIndiaPage.managedMfgTitle')}
        </h3>

        <ul className="space-y-6 pl-6">
          {[
            { title: t('whyIndiaPage.managedItem1Title'), desc: t('whyIndiaPage.managedItem1Desc') },
            { title: t('whyIndiaPage.managedItem2Title'), desc: t('whyIndiaPage.managedItem2Desc') },
            { title: t('whyIndiaPage.managedItem3Title'), desc: t('whyIndiaPage.managedItem3Desc') },
          ].map((item, index) => (
            <motion.li
              key={item.title}
              initial={{ opacity: 1, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.15 }}
              viewport={{ once: true }}
              className="relative"
            >
              {/* Number Badge */}
              <span className="absolute -left-10 top-1 w-7 h-7 flex items-center justify-center rounded-full bg-charcoal text-white text-sm font-serif font-normal shadow-md">
                {index + 1}
              </span>

              <p className="text-[#4E342E] font-serif font-normal">{item.title}</p>
              <p className="text-[#4E342E]/70 text-sm leading-relaxed">{item.desc}</p>
            </motion.li>
          ))}
        </ul>
      </motion.div>

      {/* RIGHT CARD - Sourcing Agencies (Deep Leather Brown Theme) */}
      <motion.div
        initial={{ opacity: 1, x: 60 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        whileHover={{ y: -10 }}
        className="group relative bg-gradient-to-br from-[#3E2723]/95 via-[#4E342E]/95 to-[#5D4037]/95 backdrop-blur-xl rounded-3xl p-10 shadow-xl border-2 border-[#5D4037] hover:shadow-2xl hover:shadow-[#3E2723]/40 transition-all duration-500"
      >
        {/* Side Accent Bar */}
        <div className="absolute left-0 top-10 bottom-10 w-2 rounded-full bg-gradient-to-b from-[#6D4C41] via-[#5D4037] to-[#3E2723] shadow-lg shadow-[#3E2723]/50" />

        <h3 className="text-2xl text-[#EFEBE9] mb-8 pl-6 font-serif font-medium">
          {t('whyIndiaPage.sourcingAgencyTitle')}
        </h3>

        <ul className="space-y-6 pl-6">
          {[
            { title: t('whyIndiaPage.sourcingItem1Title'), desc: t('whyIndiaPage.sourcingItem1Desc') },
            { title: t('whyIndiaPage.sourcingItem2Title'), desc: t('whyIndiaPage.sourcingItem2Desc') },
            { title: t('whyIndiaPage.sourcingItem3Title'), desc: t('whyIndiaPage.sourcingItem3Desc') },
          ].map((item, index) => (
            <motion.li
              key={item.title}
              initial={{ opacity: 1, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.15 }}
              viewport={{ once: true }}
              className="relative"
            >
              {/* Number Badge */}
              <span className="absolute -left-10 top-1 w-7 h-7 flex items-center justify-center rounded-full bg-charcoal text-white text-sm font-serif font-normal shadow-md">
                {index + 1}
              </span>

              <p className="text-[#F5E6D3] font-serif font-normal">{item.title}</p>
              <p className="text-[#F5E6D3]/70 text-sm leading-relaxed">{item.desc}</p>
            </motion.li>
          ))}
        </ul>
      </motion.div>

    </div>
  </div>
</section>

{/* The Trust Stack Section */}
<section className="relative py-24 md:py-32 bg-charcoal overflow-hidden">
  {/* Background Overlay */}
  <div className="absolute inset-0 bg-gradient-to-b bg-charcoal" />
  <div
    className="absolute inset-0 opacity-[0.03] pointer-events-none"
    style={{
      backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
    }}
  />

  <div className="relative max-w-7xl mx-auto px-4 sm:px-6 md:px-10 lg:px-16 text-center">
    {/* Top Label */}
    <motion.p
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm"
    >
      {t('whyIndiaPage.trustStackBadge')}
    </motion.p>

    {/* Title */}
    <motion.h2
      initial={{ opacity: 1, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: 0.1 }}
      className="text-4xl sm:text-5xl md:text-6xl  mb-4 text-[#FFFFFF]"
    >
      {t('whyIndiaPage.trustStackTitle')} <span className="text-saddle-tan">{t('whyIndiaPage.trustStackTitleHighlight')}</span> {t('whyIndiaPage.trustStackTitleEnd')}
    </motion.h2>

   
    <p className="text-[#D4A574]/70 mb-12 md:mb-20">{t('whyIndiaPage.trustStackSubtitle')}</p>

    {/* Cards */}
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8"
    >
      {[
        {
          icon: <ShieldCheck className="w-7 h-7 md:w-8 md:h-8 text-[#D4A574]" />,
          title: t('whyIndiaPage.trustStack1Title'),
          desc: t('whyIndiaPage.trustStack1Desc'),
          highlight: t('whyIndiaPage.trustStack1Highlight'),
        },
        {
          icon: <Leaf className="w-7 h-7 md:w-8 md:h-8 text-[#D4A574]" />,
          title: t('whyIndiaPage.trustStack2Title'),
          desc: t('whyIndiaPage.trustStack2Desc'),
          highlight: t('whyIndiaPage.trustStack2Highlight'),
          highlightShadow: true,
        },
        {
          icon: <UserCheck className="w-7 h-7 md:w-8 md:h-8 text-[#D4A574]" />,
          title: t('whyIndiaPage.trustStack3Title'),
          desc: t('whyIndiaPage.trustStack3Desc'),
          highlight: t('whyIndiaPage.trustStack3Highlight'),
        },
      ].map((card, i) => (
        <motion.div
          key={i}
          variants={staggerItem}
          whileHover={{
            y: -8,
            boxShadow: card.highlightShadow
              ? "0 20px 40px rgba(212,165,116,0.3)"
              : "0 20px 40px rgba(212,165,116,0.2)",
          }}
          className="relative group bg-[#2C1810] border border-[#D4A574]/30 rounded-xl p-8 md:p-10 backdrop-blur-xl hover:border-[#D4A574]/50 transition-all duration-300 shadow-[0_0_20px_rgba(212,165,116,0.05)]"
        >
          <div className="absolute top-6 right-6 text-[#FFFFFF]/20 text-4xl md:text-5xl font-serif font-medium">
            0{i + 1}
          </div>

          <motion.div
            whileHover={{ scale: 1.1, rotate: 5 }}
            className="w-14 h-14 md:w-16 md:h-16 rounded-full border border-[#D4A574] flex items-center justify-center mx-auto mb-6"
          >
            {card.icon}
          </motion.div>

          <h3 className="text-lg md:text-xl font-serif font-light mb-4 text-[#FFFFFF]">
            {card.title}
          </h3>
          <p className="text-[#D4A574]/80 text-xs sm:text-sm leading-relaxed mb-8 md:mb-10">
            {card.desc}
          </p>

          <div className="border-t border-[#D4A574]/30 pt-4 text-[#D4A574] tracking-widest text-xs sm:text-sm font-serif font-normal">
            {card.highlight}
          </div>
        </motion.div>
      ))}
    </motion.div>
  </div>
</section>


      {/* ChinaPlusOneSection*/}
       <section className="relative py-24 md:py-28 overflow-hidden bg-[#F5E6D3]">
      {/* Noise texture */}
      {/* Noise texture */}
<div 
  className="absolute inset-0 opacity-[0.03] pointer-events-none"
/>

<div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 lg:px-16 relative z-10">

  {/* Header */}
  <motion.div 
    initial={{ opacity: 1, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="mb-10 md:mb-16  text-center"
  >
    <p className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
      {t('whyIndiaPage.chinaPlusOneBadge')}
    </p>
    <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl  text-[#4E342E]">
      {t('whyIndiaPage.chinaPlusOneTitle')} {" "}
      <span className="text-saddle-tan">{t('whyIndiaPage.chinaPlusOneTitleHighlight')}</span> {t('whyIndiaPage.chinaPlusOneTitleEnd')}
    </h2>
  </motion.div>

  {/* Table Container */}
<div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
  <div className="rounded-2xl border border-[#D4A574]/30 bg-white overflow-hidden min-w-[600px]">
    
    {/* Table Header */}
    <div className="grid grid-cols-3 text-xs sm:text-sm uppercase tracking-widest text-[#4E342E]/70 border-b border-[#D4A574]/40 px-4 sm:px-8 py-4 sm:py-5 bg-[#F5E6D3]">
      <div>Comparison Metric</div>
      <div className="text-center">China Only</div>
      <div className="text-center text-[#D4A574]">India Diversified (Recommended)</div>
    </div>

    {/* Rows */}
    {data.map((row, index) => (
      <motion.div
        key={index}
        initial={{ opacity: 1, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.15 }}
        viewport={{ once: true }}
        whileHover={{ backgroundColor: "rgba(212,165,116,0.08)" }}
        className="grid grid-cols-3 items-center px-4 sm:px-8 py-6 sm:py-8 border-b border-[#D4A574]/20 transition-all duration-300"
      >
        {/* Left Metric */}
        <div className="flex items-center gap-3 sm:gap-4">
          <motion.div 
            whileHover={{ scale: 1.1, rotate: 5 }}
            className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[#4E342E]/10 border border-[#D4A574]/40 flex items-center justify-center"
          >
            <row.icon className="w-4 h-4 sm:w-5 sm:h-5 text-[#D4A574]" />
          </motion.div>
          <span className="text-[#4E342E] font-medium text-xs sm:text-sm md:text-base">
            {row.title}
          </span>
        </div>

        {/* China Column */}
        <div className="text-center">
          <p className="font-serif font-normal text-xs sm:text-sm md:text-base text-[#4E342E]">
            {row.china.main}
          </p>
          <p className="text-[#4E342E]/60 text-xs mt-1">{row.china.sub}</p>
        </div>

        {/* India Column */}
        <div className="text-center relative group">
          <p className="font-serif font-normal text-xs sm:text-sm md:text-base text-[#D4A574]">
            {row.india.main}
          </p>

          {row.india.tag && (
            <motion.span 
              whileHover={{ scale: 1.05 }}
              className="inline-block mt-2 px-2 sm:px-3 py-1 text-[10px] sm:text-xs rounded-full border border-[#D4A574] text-[#D4A574] group-hover:bg-[#D4A574] group-hover:text-[#4E342E] transition-all duration-300"
            >
              {row.india.tag}
            </motion.span>
          )}

          <p className="text-[#4E342E]/60 text-xs mt-2">{row.india.sub}</p>
        </div>
      </motion.div>
    ))}
  </div>
</div>

  {/* Footer Note */}
  <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mt-8 md:mt-10 text-[#D4A574]/70 text-xs sm:text-sm">
    <p className="text-[#4E342E]">{t('whyIndiaPage.chinaPlusOneFooter')}</p>
    <p className="text-[#D4A574] font-serif font-normal">{t('whyIndiaPage.chinaPlusOneFooterEnd')}</p>
  </div>
</div>

    </section>

      {/* RiskFreeStarterSection */}
      <section className="relative bg-charcoal text-white py-24 md:py-28 overflow-hidden">
      {/* Subtle radial glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-radial from-[#D4A574]/10 to-transparent rounded-full blur-3xl opacity-50" />
      </div>
      {/* Noise texture */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none text-center"
      />
      <div className="relative z-10 text-center mb-10 md:mb-16">
  <p className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
    {t('whyIndiaPage.riskFreeBadge')}
  </p>
</div>

      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-10 lg:px-16 grid grid-cols-1 lg:grid-cols-2 gap-10 md:gap-16 items-center relative z-10">

        {/* LEFT SIDE â€” MESSAGE */}
        <motion.div
          initial={{ opacity: 1, x: -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
      

          <h2 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl  leading-tight mb-4 md:mb-6 text-[#F5E6D3]">
            {t('whyIndiaPage.riskFreeTitle')}{" "}
            <span className="text-saddle-tan">{t('whyIndiaPage.riskFreeTitleHighlight')}</span>
          </h2>

          <p className="text-gray-400 text-lg mb-8">
            {t('whyIndiaPage.riskFreeSubtitle')}
          </p>
<div className="border-l-4 border-amber-400 pl-6 text-xl font-serif text-gray-200 leading-relaxed mb-8">
  {t('whyIndiaPage.riskFreeQuote')}
</div>

          <div className="flex items-center gap-3 text-gray-400 text-sm">
            <Shield className="w-4 h-4 text-amber-400" />
            {t('whyIndiaPage.riskFreeValid')}
          </div>
        </motion.div>

        {/* RIGHT SIDE â€” OFFER CARD */}
        <motion.div
          initial={{ opacity: 1, x: 60 }}
          whileInView={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="relative"
        >
          <motion.div 
            whileHover={{ y: -4, boxShadow: "0 30px 60px rgba(212,165,116,0.2)" }}
            className="relative bg-gradient-to-b from-[#4E342E] to-[#2C1810] border border-[#D4A574]/30 rounded-2xl p-6 sm:p-8 md:p-10 shadow-2xl group hover:border-[#D4A574] transition-all duration-300"
          >

            {/* Subtle Glow */}
            <div className="absolute inset-0 rounded-2xl pointer-events-none group-hover:shadow-[0_0_60px_rgba(212,165,116,0.15)] transition" />

            <p className="text-[#D4A574] tracking-widest text-xs mb-4">
              {t('whyIndiaPage.riskFreeBadge')}
            </p>

            <h3 className="text-2xl sm:text-3xl  mb-2 text-[#F5E6D3]">{t('whyIndiaPage.riskFreeCardTitle')}</h3>
            <p className="text-[#F5E6D3]/40 text-sm mb-6 md:mb-8">{t('whyIndiaPage.riskFreeCardSubtitle')}</p>

            <div className="space-y-4 sm:space-y-6 mb-8 md:mb-10">
              {[
                {
                  title: t('whyIndiaPage.riskFreeItem1Title'),
                  desc: t('whyIndiaPage.riskFreeItem1Desc'),
                },
                {
                  title: t('whyIndiaPage.riskFreeItem2Title'),
                  desc: t('whyIndiaPage.riskFreeItem2Desc'),
                },
                {
                  title: t('whyIndiaPage.riskFreeItem3Title'),
                  desc: t('whyIndiaPage.riskFreeItem3Desc'),
                },
              ].map((item, i) => (
                <div key={i} className="flex gap-3 sm:gap-4">
                  <Check className="text-[#D4A574] mt-1 w-5 h-5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-[#F5E6D3]">{item.title}</p>
                    <p className="text-[#F5E6D3]/50 text-sm">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <Link href="/bookacall">
              <motion.div 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="leather-stitch-box inline-block"
              >
                <Button className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal w-full sm:w-auto" size="lg">
                  {t('whyIndiaPage.riskFreeButton')}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>

      {/* CTA Section */}
      <section className="relative py-24 md:py-24 overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt="Leather craftsmanship"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-charcoal/85" />
        </div>
        
        <div className="container mx-auto px-4 sm:px-6 md:px-10 lg:px-16 relative z-10">
          <motion.div
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl mx-auto text-center"
          >
            <h2 className=" text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige mt-4 mb-6 leading-tight">
              {t('whyIndiaPage.finalCtaTitle')} <span className="text-saddle-tan">{t('whyIndiaPage.finalCtaTitleHighlight')}</span>
            </h2>
            <p className="text-warm-beige/80 text-base sm:text-lg mb-6 md:mb-8 leading-relaxed">
              {t('whyIndiaPage.finalCtaDesc')}
            </p>
            <Link href="/bookacall">
              <motion.div 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="leather-stitch-box inline-block"
              >
                <Button className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal w-full sm:w-auto" size="lg">
                  {t('whyIndiaPage.finalCtaButton')}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </motion.div>
            </Link>
          </motion.div>
        </div>
      </section>
    </>
  );
};

export default WhyIndia;
