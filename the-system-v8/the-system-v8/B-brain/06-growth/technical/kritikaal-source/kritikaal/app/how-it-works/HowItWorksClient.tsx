"use client";

import { useState } from "react";

import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ChevronRight, ArrowRight, PenTool, Layers, Factory, Search, Ship, CheckCircle, ShoppingBag, Wallet, Award, X, Laptop, AlertTriangle, Ban, Quote, Truck, Palette, Box, ClipboardCheck, PackageCheck, Navigation, PhoneCall, DollarSign } from "lucide-react";
import leatherTexture from "@/assets/leather-work.jpg";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";

// Real images for process steps
import leadBookingImg from "@/assets/howitwork/lead&call-booking.jpeg";
import discoveryImg from "@/assets/howitwork/discovery&qualification.jpeg";
import sampleDevImg from "@/assets/howitwork/sample-development.jpeg";
import quotationImg from "@/assets/howitwork/quotation.jpeg";
import orderConfImg from "@/assets/howitwork/order-confirmation.jpeg";
import productionQCImg from "@/assets/howitwork/production&qc.jpeg";
import logisticsExportImg from "@/assets/howitwork/logistic&export.jpeg";
import deliveryRetentionImg from "@/assets/howitwork/delivery&retention.jpeg";

const HowItWorks = () => {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState<number>(0);
  const [hoveredProduct, setHoveredProduct] = useState<string | null>(null);

  const trackingSteps = [
    { id: 1, name: "Booking", icon: PhoneCall },
    { id: 2, name: "Discovery", icon: Search },
    { id: 3, name: "Sampling", icon: Palette },
    { id: 4, name: "Quotation", icon: DollarSign },
    { id: 5, name: "Confirmation", icon: CheckCircle },
    { id: 6, name: "Production", icon: Factory },
    { id: 7, name: "Logistics", icon: Ship },
    { id: 8, name: "Delivery", icon: Truck },
  ];

  const processSteps = [
    {
      icon: PhoneCall,
      number: "01",
      title: "Lead & Call Booking",
      description: "Share your manufacturing requirements and our team responds within 24 hours to begin the sourcing process immediately.",
      features: [
        "Your brief reaches us within 24 hours",
        "No waiting",
        "No gatekeepers",
      ],
      image: leadBookingImg,
    },
    {
      icon: Search,
      number: "02",
      title: "Discovery & Qualification",
      description: "We evaluate your product category, production goals, compliance needs, and match you with the most suitable leather manufacturing cluster in India.",
      features: [
        "We confirm your product",
        "The right India cluster",
        "Compliance requirements confirmation",
      ],
      image: discoveryImg,
    },
    {
      icon: Palette,
      number: "03",
      title: "Sample Development",
      description: "Our artisans develop and dispatch your product sample within 10–14 working days with fully tracked international shipping.",
      features: [
        "Physical sample in 10–14 working days",
        "DHL tracked to your door",
        "Iterative refinement",
      ],
      image: sampleDevImg,
    },
    {
      icon: DollarSign,
      number: "04",
      title: "Quotation",
      description: "Receive a transparent cost structure covering production, freight, duties, compliance, and export-related expenses before placing an order.",
      features: [
        "Full landed cost breakdown",
        "FOB, freight, import duty",
        "Compliance costs included",
      ],
      image: quotationImg,
    },
    {
      icon: CheckCircle,
      number: "05",
      title: "Order Confirmation",
      description: "Once payment is secured, your production order is officially activated with escrow-backed protection until final approval.",
      features: [
        "Work order within 24 hours",
        "Funds held in escrow account",
        "Release after final AQL approval",
      ],
      image: orderConfImg,
    },
    {
      icon: Factory,
      number: "06",
      title: "Production & QC",
      description: "Your order undergoes strict AQL quality inspections during and after production, supported by detailed reports and guaranteed accountability.",
      features: [
        "AQL 2.5 at 30% and final",
        "Full photo report before packing",
        "Double unit cost back for defects",
      ],
      image: productionQCImg,
    },
    {
      icon: Ship,
      number: "07",
      title: "Logistics & Export",
      description: "All export documentation, compliance certifications, freight coordination, and shipment paperwork are completed before dispatch.",
      features: [
        "REACH, CA65, GSP Form A",
        "Commercial Invoice, Bill of Lading",
        "Pre-loading documentation",
      ],
      image: logisticsExportImg,
    },
    {
      icon: Truck,
      number: "08",
      title: "Delivery & Retention",
      description: "Your products are delivered on schedule and to agreed standards while we continue supporting your future manufacturing growth.",
      features: [
        "On time, quality, and budget",
        "Immediate next order planning",
        "Long-term partnership focus",
      ],
      image: deliveryRetentionImg,
    },
  ];


  const notManufactured = [
    { item: "Electronics or tech accessories", icon: Laptop },
    { item: "Regulated products (medical, food-contact, children's goods)", icon: AlertTriangle },
    { item: "Unrelated categories outside leather goods", icon: Ban }
  ];


  return (
    <>
      {/* Simple Hero Section */}
      <section className="relative pt-32 pb-24 lg:pt-48 lg:pb-32 overflow-hidden bg-charcoal min-h-[60vh] flex items-center">
        {/* Background */}
        <div className="absolute inset-0">
          <div
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }}
          />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>

        {/* Content */}
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="flex justify-start">
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="max-w-4xl text-left"
            >
              {/* Badge */}
              <motion.span
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-6 block"
              >
                {t('howItWorksPage.badge')}
              </motion.span>

              {/* Heading */}
              <motion.h1
                className="font-serif text-4xl md:text-5xl lg:text-7xl text-warm-beige mb-8 leading-tight"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
                {t('howItWorksPage.title')}{' '}
                <span className="text-saddle-tan">
                  {t('howItWorksPage.titleHighlight')}
                </span>
              </motion.h1>

              {/* Description */}
              <motion.p
                className="text-xl md:text-2xl text-[#F5E6D3]/80 leading-relaxed mb-10 max-w-2xl"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                {t('howItWorksPage.description')}
              </motion.p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tracking Streamline */}
      <section className="py-24 md:py-16 bg-charcoal relative overflow-hidden">
        {/* Subtle background pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,#D4A574_1px,transparent_0)] bg-[length:24px_24px]" />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-8 md:mb-12"
          >
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-xs md:text-sm mb-2 block">
              {t('howItWorksPage.trackingBadge')}
            </span>
            <h2 className="font-serif text-2xl md:text-3xl lg:text-4xl text-warm-beige mb-2 md:mb-3">
              {t('howItWorksPage.trackingTitle')}
            </h2>
            <p className="text-warm-beige/60 text-xs md:text-sm max-w-xl mx-auto">{t('howItWorksPage.trackingSubtitle')}</p>
          </motion.div>

          {/* Horizontal Streamline */}
          <div className="relative max-w-6xl mx-auto">
            {/* Connecting Line Background - Hidden on mobile */}
            <div className="absolute top-10 left-[5%] right-[5%] h-1 bg-deep-leather-brown/50 hidden lg:block rounded-full" />

            {/* Animated Progress Line */}
            <motion.div
              className="absolute top-10 left-[5%] h-1 bg-gradient-to-r from-saddle-tan via-saddle-tan to-saddle-tan/80 hidden lg:block rounded-full"
              initial={{ width: 0 }}
              whileInView={{ width: "90%" }}
              viewport={{ once: true }}
              transition={{ duration: 2, ease: "easeOut" }}
            />

            {/* Animated Glow Effect */}
            <motion.div
              className="absolute top-9 h-3 bg-saddle-tan/20 blur-sm hidden lg:block rounded-full"
              initial={{ left: "5%", width: 0 }}
              whileInView={{ width: "90%" }}
              viewport={{ once: true }}
              transition={{ duration: 2, ease: "easeOut" }}
            />

            {/* Steps - Grid on mobile, flex on larger screens */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4 md:gap-6 lg:gap-2">
              {trackingSteps.map((step, index) => (
                <motion.div
                  key={step.id}
                  initial={{ opacity: 1, scale: 0.8, y: 30 }}
                  whileInView={{ opacity: 1, scale: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{
                    delay: index * 0.15,
                    duration: 0.5,
                    type: "spring",
                    stiffness: 100
                  }}
                  className="flex flex-col items-center group relative"
                >
                  {/* Circle with Icon */}
                  <motion.div
                    className="relative z-10 w-14 h-14 md:w-16 md:h-16 rounded-full bg-deep-leather-brown border-3 md:border-4 border-saddle-tan flex items-center justify-center shadow-xl mb-3 md:mb-4 group-hover:border-warm-beige transition-colors duration-300"
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {/* Pulse animation */}
                    <motion.div
                      className="absolute inset-0 rounded-full bg-saddle-tan/30"
                      animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
                    />
                    <step.icon className="w-5 h-5 md:w-6 md:h-6 text-warm-beige relative z-10" />
                  </motion.div>

                  {/* Step Name */}
                  <span className="text-warm-beige font-serif font-normal text-xs md:text-sm text-center group-hover:text-saddle-tan transition-colors duration-300">
                    {step.name}
                  </span>

                  {/* Step Number */}
                  <span className="text-saddle-tan/70 text-[10px] md:text-[11px] mt-1 font-medium">
                    {t('howItWorksPage.trackingStepLabel')} {step.id}
                  </span>

                  {/* Arrow to Next Step (Desktop only) */}
                  {index < trackingSteps.length - 1 && (
                    <div className="hidden lg:flex absolute top-8 left-[50%] w-[calc(100%+8px)] justify-center items-center pointer-events-none -translate-y-1/2 z-0">
                      <motion.div
                        animate={{ x: [0, 4, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: index * 0.2 }}
                      >
                        <ChevronRight className="w-5 h-5 text-saddle-tan" strokeWidth={2.5} />
                      </motion.div>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Process Steps */}
      <section className="py-24 md:py-24 bg-warm-beige">
        <div className="container mx-auto px-4">
          <div className="space-y-12 md:space-y-16">
            {processSteps.map((step, index) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 1, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className={`grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 items-center ${index % 2 === 1 ? "lg:flex-row-reverse" : ""
                  }`}
              >
                <div className={index % 2 === 1 ? "lg:order-2" : ""}>
                  <div className="flex items-center gap-3 md:gap-4 mb-4">
                    <div className="w-12 h-12 md:w-16 md:h-16 rounded-xl md:rounded-2xl bg-primary/10 flex items-center justify-center">
                      <step.icon className="w-6 h-6 md:w-8 md:h-8 text-primary" />
                    </div>
                    <span className="font-serif text-3xl md:text-5xl font-medium text-muted-foreground/20">
                      {step.number}
                    </span>
                  </div>
                  <h3 className="font-serif text-2xl md:text-3xl text-foreground mb-3 md:mb-4">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed mb-4 md:mb-6 text-sm md:text-base">
                    {step.description}
                  </p>
                  <div className="grid grid-cols-2 gap-2 md:gap-3">
                    {step.features.map((feature) => (
                      <div key={feature} className="flex items-center gap-2">
                        <CheckCircle className="w-3 h-3 md:w-4 md:h-4 text-primary flex-shrink-0" />
                        <span className="text-xs md:text-sm text-foreground">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className={`relative ${index % 2 === 1 ? "lg:order-1" : ""}`}>
                  <div className="absolute -inset-4 bg-gradient-to-r from-primary/10 to-gold/10 rounded-3xl blur-2xl" />
                  <div className="relative bg-card rounded-2xl p-4 md:p-8 shadow-card border border-border/50 overflow-hidden">
                    <img
                      src={step.image.src}
                      alt={step.title}
                      className="w-full h-48 md:h-64 lg:h-72 object-cover rounded-xl"
                    />
                  </div>
                </div>

              </motion.div>
            ))}
          </div>
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
            <h2 className="font-serif text-4xl md:text-5xl lg:text-6xl text-warm-beige mt-4 mb-6 leading-tight">
              {t('whyIndiaPage.visionTitle')} <span className="text-saddle-tan">{t('whyIndiaPage.visionTitleHighlight')}</span>
            </h2>
            <p className="text-warm-beige/80 mb-8">
              {t('whyIndiaPage.visionSubtitle')}
            </p>
            <Link href="/bookacall">
              <div className="leather-stitch-box inline-block">
                <Button className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal" size="lg">
                  {t('whyIndiaPage.visionButton')}
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

export default HowItWorks;
