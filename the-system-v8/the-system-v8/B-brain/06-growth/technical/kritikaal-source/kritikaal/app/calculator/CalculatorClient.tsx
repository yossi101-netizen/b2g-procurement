"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ChevronDown, AlertTriangle, ShieldCheck, DollarSign, PackageOpen, Globe, ArrowRight, Info, TrendingUp, Shield, Check, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import Image from "next/image";
// jsPDF and autoTable removed from static imports to reduce JS bloat (Fixes Failure #3)
import { useTranslation } from "@/contexts/TranslationContext";

// Import product images
import walletImg from "@/assets/Calculator/classic-mens-wallet.webp";
import beltImg from "@/assets/Calculator/leather-belt.jpeg";
import handbagImg from "@/assets/Calculator/daily-crossbody-bag.jpeg";
import backpackImg from "@/assets/Calculator/structured-tote-bag.jpeg";
import laptopSleeveImg from "@/assets/Calculator/classic-leather-backpack.jpeg";
import travelDuffelImg from "@/assets/Calculator/leather-travel-duffel.png";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";

const products = {
  wallet: {
    name: "Classic Men's Wallet",
    chinaBase: 4,
    indiaBase: 4.8,
    image: walletImg,
    designs: "12 Unique Designs"
  },
  belt: {
    name: "Leather Belt",
    chinaBase: 6,
    indiaBase: 7.2,
    image: beltImg,
    designs: "8 Unique Designs"
  },
  handbag: {
    name: "Daily CrossBody Bag",
    chinaBase: 18,
    indiaBase: 21,
    image: handbagImg,
    designs: "10 Unique Designs"
  },
  backpack: {
    name: "Structured Tote Bag",
    chinaBase: 22,
    indiaBase: 25,
    image: backpackImg,
    designs: "15 Unique Designs"
  },
  laptopsleeve: {
    name: "Classic Leather Backpack",
    chinaBase: 10,
    indiaBase: 11.5,
    image: laptopSleeveImg,
    designs: "6 Unique Designs"
  },
  passportcover: {
    name: "Leather Travel Duffel",
    chinaBase: 3.5,
    indiaBase: 4.2,
    image: travelDuffelImg,
    designs: "4 Unique Designs"
  }
};

const countryMultipliers = {
  usa: { label: "USA", rate: 0.18, symbol: "$" },
  uk: { label: "UK", rate: 0.16, symbol: "£" },
  germany: { label: "Germany", rate: 0.20, symbol: "€" },
  uae: { label: "UAE", rate: 0.10, symbol: "د.إ" },
  australia: { label: "Australia", rate: 0.15, symbol: "A$" }
};

export default function CalculatorClient() {
  const { t } = useTranslation();
  const [selectedProduct, setSelectedProduct] = useState<keyof typeof products>("handbag");
  const [quantity, setQuantity] = useState(500);
  const [selectedCountry, setSelectedCountry] = useState<keyof typeof countryMultipliers>("usa");
  const [showResults, setShowResults] = useState(false);

  const calculateCosts = () => {
    const p = products[selectedProduct];
    const qty = quantity || 0;

    const chinaBaseTotal = p.chinaBase * qty;
    const chinaFreight = chinaBaseTotal * 0.12;
    const chinaDuties = chinaBaseTotal * countryMultipliers[selectedCountry].rate;
    const chinaWarehousing = qty * 0.50;
    const chinaQcRisk = chinaBaseTotal * 0.08;
    const chinaDelayRisk = chinaBaseTotal * 0.05;
    const chinaCommOverhead = chinaBaseTotal * 0.04;
    const chinaSamplingCost = 150;
    const chinaReorderRisk = chinaBaseTotal * 0.06;
    const chinaCurrencyLoss = chinaBaseTotal * 0.02;
    const chinaLogisticsCoord = chinaBaseTotal * 0.03;

    const chinaTotal = chinaBaseTotal + chinaFreight + chinaDuties + chinaWarehousing + chinaQcRisk + chinaDelayRisk + chinaCommOverhead + chinaSamplingCost + chinaReorderRisk + chinaCurrencyLoss + chinaLogisticsCoord;

    const indiaBaseTotal = p.indiaBase * qty;
    const indiaServiceFee = indiaBaseTotal * 0.07;
    const indiaLogistics = indiaBaseTotal * 0.05;
    const indiaQc = indiaBaseTotal * 0.02;
    const indiaCompliance = indiaBaseTotal * 0.02;

    const indiaTotal = indiaBaseTotal + indiaServiceFee + indiaLogistics + indiaQc + indiaCompliance;

    const savings = chinaTotal - indiaTotal;
    const savingsPercent = (savings / chinaTotal) * 100;

    return {
      china: { base: chinaBaseTotal, freight: chinaFreight, duties: chinaDuties, qcRisk: chinaQcRisk, delayRisk: chinaDelayRisk, comm: chinaCommOverhead, total: chinaTotal },
      india: { base: indiaBaseTotal, serviceFee: indiaServiceFee, logistics: indiaLogistics, qc: indiaQc, compliance: indiaCompliance, duties: 0, total: indiaTotal },
      savings,
      savingsPercent
    };
  };

  const results = calculateCosts();

  const handleCalculate = () => {
    setShowResults(true);
    setTimeout(() => {
      document.getElementById('step-3')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
  };

  const handleDownloadPDF = async () => {
    // Dynamically import jsPDF and autoTable ONLY when needed (Fixes Failure #3)
    const { jsPDF } = await import("jspdf");
    const autoTable = (await import("jspdf-autotable")).default;

    const doc = new jsPDF();
    const product = products[selectedProduct];
    const country = countryMultipliers[selectedCountry];

    // Header
    doc.setFontSize(24);
    doc.text("KRITIKAAL", 14, 22);
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text("Managed Leather Manufacturing in India, Under Full Responsibility.", 14, 28);
    
    doc.setFontSize(18);
    doc.setTextColor(0, 0, 0);
    doc.text("Cost Comparison Report", 14, 40);
    
    doc.setFontSize(10);
    doc.setTextColor(120, 120, 120);
    doc.text(`Generated on ${new Date().toLocaleDateString()}`, 14, 46);

    // Project Parameters
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text("Project Parameters", 14, 60);

    autoTable(doc, {
      startY: 64,
      head: [['Parameter', 'Value']],
      body: [
        ['Product Category', product.name],
        ['Production Quantity', `${quantity} Units`],
        ['Destination Market', country.label],
      ],
      theme: 'grid',
      headStyles: { fillColor: [193, 138, 93], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [255, 255, 255] },
      margin: { left: 14 }
    });

    let currentY = (doc as any).lastAutoTable.finalY + 15;

    // Unmanaged China Import Breakdown
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text("Unmanaged China Import Breakdown", 14, currentY);

    autoTable(doc, {
      startY: currentY + 4,
      head: [['Cost Factor', 'Amount']],
      body: [
        ['Base Manufacturing (FOB)', formatCurrency(results.china.base)],
        ['Ocean Freight & Logistics', formatCurrency(results.china.freight)],
        ['Import Duties & Tariffs', formatCurrency(results.china.duties)],
        ['QC Failure & Rework Risk', formatCurrency(results.china.qcRisk)],
        ['Shipment Delay Penalties', formatCurrency(results.china.delayRisk)],
        ['Communication Overhead', formatCurrency(results.china.comm)],
      ],
      foot: [
        ['True Landed Cost', formatCurrency(results.china.total)]
      ],
      theme: 'grid',
      headStyles: { fillColor: [239, 68, 68], textColor: [255, 255, 255] },
      footStyles: { fillColor: [250, 250, 250], textColor: [0, 0, 0], fontStyle: 'bold' },
      margin: { left: 14 }
    });

    currentY = (doc as any).lastAutoTable.finalY + 15;

    // KRITIKAAL Managed India Production
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0);
    doc.text("KRITIKAAL Managed India Production", 14, currentY);

    autoTable(doc, {
      startY: currentY + 4,
      head: [['Cost Factor', 'Amount']],
      body: [
        ['Production Cost (Landed)', formatCurrency(results.india.base)],
        ['Full Managed Service Fee', formatCurrency(results.india.serviceFee)],
        ['Streamlined Logistics', formatCurrency(results.india.logistics)],
        ['Centralized AQL-2.5 QC', formatCurrency(results.india.qc)],
        ['Compliance & Certification', formatCurrency(results.india.compliance)],
        ['Defect Allowance', formatCurrency(0)],
      ],
      foot: [
        ['True Landed Cost', formatCurrency(results.india.total)]
      ],
      theme: 'grid',
      headStyles: { fillColor: [193, 138, 93], textColor: [255, 255, 255] },
      footStyles: { fillColor: [250, 250, 250], textColor: [0, 0, 0], fontStyle: 'bold' },
      margin: { left: 14 }
    });

    currentY = (doc as any).lastAutoTable.finalY + 20;
    
    // Savings
    doc.setFontSize(16);
    doc.setTextColor(16, 185, 129); // Emerald 500
    doc.text(`Total Savings: ${formatCurrency(results.savings)} (${results.savingsPercent.toFixed(1)}% cheaper)`, 14, currentY);

    doc.save("KRITIKAAL_Cost_Comparison.pdf");
  };

  return (
    <>
      <section className="relative pt-32 pb-24 lg:pt-48 lg:pb-32 overflow-hidden min-h-[80vh] flex items-center">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
          <div className="absolute inset-0 bg-charcoal/90" />
        </div>
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="flex justify-start">
            <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8 }} className="max-w-4xl text-left">
              <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-6 block">{t('calculatorPage.badge')}</span>
              <h1 className="font-serif text-4xl md:text-5xl lg:text-7xl text-warm-beige mb-6 leading-tight">
                {t('calculatorPage.title')} <span className="text-saddle-tan">{t('calculatorPage.titleHighlight')}</span>
              </h1>
              <p className="text-xl text-warm-beige/80 leading-relaxed mb-10 max-w-2xl">{t('calculatorPage.subtitle')}</p>
            </motion.div>
          </div>
        </div>
      </section>

      <section id="step-1" className="relative py-12 lg:py-16 bg-charcoal overflow-hidden scroll-mt-20">
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className={`mx-auto transition-all duration-700 ${showResults ? "max-w-[1500px]" : "max-w-4xl"}`}>
            <div className={`grid grid-cols-1 ${showResults ? "xl:grid-cols-2" : ""} gap-10 xl:gap-16 items-start`}>
              <div className="space-y-12 md:space-y-16">
                <div className="bg-[#1A1A1A]/80 backdrop-blur-md rounded-2xl border border-white/5 p-4 sm:p-6 lg:p-8 flex-1">
                  <div className="flex items-center gap-4 mb-4 sm:mb-6">
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-saddle-tan/20 flex items-center justify-center text-saddle-tan font-serif font-bold text-lg">1</div>
                    <h2 className="text-lg sm:text-xl md:text-2xl font-serif text-white">{t('calculatorPage.step1Title')}</h2>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                    {Object.entries(products).map(([key, product]) => (
                      <button key={key} onClick={() => { setSelectedProduct(key as keyof typeof products); setShowResults(false); }} className={`group relative flex flex-col rounded-2xl overflow-hidden border-2 transition-all ${selectedProduct === key ? "border-saddle-tan" : "border-white/5"}`}>
                        <div className="relative aspect-[4/3] bg-black/20">
                          <Image src={product.image} alt={product.name} fill className="object-cover" />
                        </div>
                        <div className="py-2.5 px-3 text-center bg-[#1A110D]">
                          <span className="font-serif text-xs md:text-sm text-warm-beige/80">{product.name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="bg-[#1A1A1A]/80 backdrop-blur-md rounded-2xl border border-white/5 p-4 sm:p-6 lg:p-8 flex-1">
                  <div className="flex items-center gap-4 mb-4 sm:mb-6">
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-saddle-tan/20 flex items-center justify-center text-saddle-tan font-serif font-bold text-lg">2</div>
                    <h2 className="text-lg sm:text-xl md:text-2xl font-serif text-white">{t('calculatorPage.step2Title')}</h2>
                  </div>
                  <div className="grid md:grid-cols-2 gap-6">
                     <select value={selectedCountry} onChange={(e) => { setSelectedCountry(e.target.value as keyof typeof countryMultipliers); setShowResults(false); }} className="w-full bg-black/40 border border-saddle-tan/20 rounded-xl p-4 text-warm-beige">
                       {Object.entries(countryMultipliers).map(([key, data]) => <option key={key} value={key}>{data.label}</option>)}
                     </select>
                     <input type="number" value={quantity} onChange={(e) => { setQuantity(parseInt(e.target.value) || 0); setShowResults(false); }} className="w-full bg-black/40 border border-saddle-tan/20 rounded-xl p-4 text-warm-beige" />
                  </div>
                </div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                  <button
                    onClick={handleCalculate}
                    className="w-full bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-bold py-4 sm:py-5 rounded-xl transition-all duration-300 flex items-center justify-center group text-sm sm:text-base"
                  >
                    {showResults ? t('calculatorPage.recalculateButton') : t('calculatorPage.generateButton')}
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </button>
                </motion.div>
              </div>

              <AnimatePresence>
                {showResults && (
                  <motion.div id="step-3" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 40 }} className="xl:sticky xl:top-32 space-y-8">
                                      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-saddle-tan flex items-center justify-center text-charcoal font-serif font-bold text-lg">3</div>
                      <h2 className="text-lg sm:text-xl md:text-2xl font-serif text-white">{t('calculatorPage.step3Title')}</h2>
                    </div>
                    <button onClick={handleDownloadPDF} className="flex items-center gap-2 text-saddle-tan hover:text-white transition-colors text-xs sm:text-sm bg-white/5 px-4 py-2 rounded-lg border border-white/10 hover:border-saddle-tan/50 w-full sm:w-auto justify-center">
                      <Download className="w-4 h-4" />
                      {t('calculatorPage.downloadPdf')}
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* China Breakdown */}
                      <div className="bg-[#1A110D] border border-white/5 rounded-2xl overflow-hidden flex flex-col">
                        <div className="p-5 border-b border-white/5">
                          <div className="flex items-center gap-2 mb-2 text-warm-beige/60 text-xs font-bold uppercase tracking-wider">
                            <span className="bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded text-[10px]">CN</span>
                            {t('calculatorPage.unmanagedChina')}
                          </div>
                          <div className="text-3xl font-serif text-red-400">{formatCurrency(results.china.total)}</div>
                        </div>

                        <div className="p-5 flex-grow bg-white/[0.02]">
                          <div className="space-y-3">
                            <BreakdownRow label={t('calculatorPage.fobCost')} value={results.china.base} risk={false} />
                            <BreakdownRow label={t('calculatorPage.shipping')} value={results.china.freight} risk={false} />
                            <BreakdownRow label={t('calculatorPage.duty')} value={results.china.duties} risk={false} />
                            <BreakdownRow label="QC Failure & Rework Risk" value={results.china.qcRisk} risk />
                            <BreakdownRow label="Shipment Delay Penalties" value={results.china.delayRisk} risk />
                            <BreakdownRow label="Communication Overhead" value={results.china.comm} risk />
                            
                            <div className="pt-3 mt-3 border-t border-white/5">
                              <BreakdownRow label={t('calculatorPage.totalPerUnit')} value={results.china.total} risk={false} isTotal />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* India Breakdown */}
                      <div className="bg-[#1A110D] border border-saddle-tan/30 rounded-2xl overflow-hidden flex flex-col relative shadow-lg shadow-saddle-tan/5">
                        <div className="p-5 border-b border-saddle-tan/10 bg-saddle-tan/[0.02] relative z-10">
                          <div className="flex items-center gap-2 mb-2 text-warm-beige/80 text-xs font-bold uppercase tracking-wider">
                            <span className="bg-saddle-tan/20 text-saddle-tan px-1.5 py-0.5 rounded text-[10px]">IN</span>
                            {t('calculatorPage.managedIndia')}
                          </div>
                          <div className="text-3xl font-serif text-saddle-tan">{formatCurrency(results.india.total)}</div>
                        </div>

                        <div className="p-5 flex-grow relative z-10 bg-white/[0.02]">
                          <div className="space-y-3">
                            <BreakdownRow label={t('calculatorPage.fobCost')} value={results.india.base} />
                            <BreakdownRow label="Full Managed Service Fee" value={results.india.serviceFee} />
                            <BreakdownRow label="Streamlined Logistics" value={results.india.logistics} />
                            <BreakdownRow label="Centralized AQL-2.5 QC" value={results.india.qc} />
                            <BreakdownRow label="Compliance & Cert." value={results.india.compliance} />

                            <div className="pt-3 mt-3 border-t border-saddle-tan/20">
                              <BreakdownRow label={t('calculatorPage.totalPerUnit')} value={results.india.total} isTotal />
                            </div>
                          </div>
                        </div>
                      </div>
                  </div>
                  {/* Savings Banner AT BOTTOM */}
                  <div className="bg-[#0A1A12] border border-emerald-500/20 rounded-2xl p-5 flex items-center justify-between">
                    <div>
                        <div className="text-emerald-500/70 text-xs mb-1">{t('calculatorPage.savingsBanner')}</div>
                        <div className="text-2xl font-bold text-emerald-400">{formatCurrency(results.savings)}</div>
                        <div className="text-emerald-500/50 text-[10px] mt-1">{t('calculatorPage.savingsBannerSub')}</div>
                    </div>
                    <div className="bg-emerald-500/10 text-emerald-400 text-xs font-bold px-3 py-1.5 rounded-full border border-emerald-500/20">
                        {results.savingsPercent.toFixed(1)}% cheaper
                    </div>
                  </div>

                </motion.div>
              )}
            </AnimatePresence>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

function BreakdownRow({ label, value, risk = false, isTotal = false }: { label: string; value: number; risk?: boolean; isTotal?: boolean }) {
  return (
    <div className="flex justify-between items-center group">
      <span className={`text-xs md:text-sm ${isTotal ? "text-warm-beige font-bold" : risk ? "text-red-400" : "text-warm-beige/60"}`}>
        {label}
      </span>
      <span className={`font-mono text-xs md:text-sm transition-colors ${isTotal ? "text-warm-beige font-bold" : risk ? "text-red-400" : "text-warm-beige/90"}`}>
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(value)}
      </span>
    </div>
  );
}
