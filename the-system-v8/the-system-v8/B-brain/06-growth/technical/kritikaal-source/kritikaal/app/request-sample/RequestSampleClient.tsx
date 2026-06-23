"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle, Package, Send, Truck } from "lucide-react";

const PRODUCT_TYPES = [
  { value: "", label: "Select product type" },
  { value: "footwear", label: "Leather Footwear (Formal, Casual, Boots)" },
  { value: "bags", label: "Leather Bags & Handbags" },
  { value: "wallets", label: "Leather Wallets & Small Accessories" },
  { value: "belts", label: "Leather Belts" },
  { value: "garments", label: "Leather Garments (Jackets & Apparel)" },
  { value: "accessories", label: "Custom Leather Accessories" },
];

const STEPS = [
  {
    icon: Send,
    step: "01",
    title: "Submit Requirements",
    description:
      "Share your product specs, reference images, materials, and target quantity. Our team reviews your brief within 24 hours.",
  },
  {
    icon: Package,
    step: "02",
    title: "Sample Development",
    description:
      "We select the right factory cluster (Agra, Kanpur, or Kolkata), source materials, and develop your prototype — typically 15–25 days.",
  },
  {
    icon: Truck,
    step: "03",
    title: "Production & Delivery",
    description:
      "After sample approval, we manage bulk production with in-process QC (AQL 2.5), final inspection, and export documentation.",
  },
];

export default function RequestSampleClient() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    productType: "",
    quantity: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Backend integration placeholder
    setSubmitted(true);
  };

  return (
    <>
      {/* ── HERO ────────────────────────────── */}
      <section
        id="request-sample-hero"
        className="relative pt-40 pb-20 overflow-hidden"
      >
        <div className="absolute inset-0 z-0">
          <img
            src="/leather-bg.jpg"
            alt="Premium leather manufacturing"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-charcoal/97 via-charcoal/90 to-charcoal/75" />
        </div>

        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <span className="inline-block text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm mb-4">
            Sample Development
          </span>
          <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige leading-tight mb-6 max-w-3xl">
            Start Your Leather Sample Development{" "}
            <span className="text-saddle-tan">with KRITIKAAL</span>
          </h1>
          <p className="text-warm-beige/80 text-base sm:text-lg font-serif font-light leading-relaxed max-w-2xl">
            Submit your brief and receive a dedicated sample development plan —
            from factory selection and material sourcing to prototype delivery
            and bulk production.
          </p>
        </div>
      </section>

      {/* ── FORM + PROCESS ──────────────────── */}
      <section
        className="relative py-20 overflow-hidden"
        style={{
          background:
            "radial-gradient(circle at top, #4A3228 0%, #3E2723 35%, #2C1810 70%, #1A0F0A 100%)",
        }}
      >
        <div className="container mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-5 gap-12 max-w-7xl mx-auto">

            {/* Form */}
            <div className="lg:col-span-3">
              <div className="bg-[#2C1810]/80 backdrop-blur-sm border border-[#D4A574]/20 rounded-2xl p-6 sm:p-8 shadow-2xl">
                <h2 className="font-serif text-2xl sm:text-3xl text-warm-beige mb-2">
                  Request a Sample
                </h2>
                <p className="text-warm-beige/55 text-sm mb-8 font-serif font-light">
                  Fields marked * are required. We respond within 24 hours.
                </p>

                {submitted ? (
                  <div className="text-center py-12">
                    <CheckCircle className="w-16 h-16 text-saddle-tan mx-auto mb-4" />
                    <h3 className="font-serif text-2xl text-warm-beige mb-3">
                      Request Received!
                    </h3>
                    <p className="text-warm-beige/70 mb-6 font-serif font-light">
                      Our team will review your brief and contact you within 24
                      hours.
                    </p>
                    <Link
                      href="/"
                      className="inline-flex items-center gap-2 text-saddle-tan hover:text-saddle-tan/80 transition-colors font-serif"
                    >
                      <ArrowRight className="w-4 h-4 rotate-180" />
                      Back to Home
                    </Link>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid sm:grid-cols-2 gap-5">
                      <div>
                        <label
                          htmlFor="rs-name"
                          className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                        >
                          Name *
                        </label>
                        <input
                          id="rs-name"
                          name="name"
                          type="text"
                          required
                          value={form.name}
                          onChange={handleChange}
                          placeholder="Your full name"
                          className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige placeholder-warm-beige/30 focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif"
                        />
                      </div>
                      <div>
                        <label
                          htmlFor="rs-email"
                          className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                        >
                          Email *
                        </label>
                        <input
                          id="rs-email"
                          name="email"
                          type="email"
                          required
                          value={form.email}
                          onChange={handleChange}
                          placeholder="you@company.com"
                          className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige placeholder-warm-beige/30 focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif"
                        />
                      </div>
                    </div>

                    <div>
                      <label
                        htmlFor="rs-company"
                        className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                      >
                        Company{" "}
                        <span className="text-warm-beige/40">(optional)</span>
                      </label>
                      <input
                        id="rs-company"
                        name="company"
                        type="text"
                        value={form.company}
                        onChange={handleChange}
                        placeholder="Your brand or company name"
                        className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige placeholder-warm-beige/30 focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif"
                      />
                    </div>

                    <div className="grid sm:grid-cols-2 gap-5">
                      <div>
                        <label
                          htmlFor="rs-product"
                          className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                        >
                          Product Type *
                        </label>
                        <select
                          id="rs-product"
                          name="productType"
                          required
                          value={form.productType}
                          onChange={handleChange}
                          className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif appearance-none cursor-pointer"
                        >
                          {PRODUCT_TYPES.map((opt) => (
                            <option
                              key={opt.value}
                              value={opt.value}
                              disabled={opt.value === ""}
                              className="bg-[#1A0F0A]"
                            >
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label
                          htmlFor="rs-quantity"
                          className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                        >
                          Estimated Quantity *
                        </label>
                        <input
                          id="rs-quantity"
                          name="quantity"
                          type="text"
                          required
                          value={form.quantity}
                          onChange={handleChange}
                          placeholder="e.g. 500 units"
                          className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige placeholder-warm-beige/30 focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif"
                        />
                      </div>
                    </div>

                    <div>
                      <label
                        htmlFor="rs-message"
                        className="block text-warm-beige/80 text-sm mb-1.5 font-serif"
                      >
                        Requirements *
                      </label>
                      <textarea
                        id="rs-message"
                        name="message"
                        required
                        rows={5}
                        value={form.message}
                        onChange={handleChange}
                        placeholder="Describe your product — materials, colours, target market, reference styles..."
                        className="w-full bg-[#1A0F0A] border border-[#D4A574]/30 rounded-lg px-4 py-3 text-warm-beige placeholder-warm-beige/30 focus:outline-none focus:border-saddle-tan transition-colors text-sm font-serif resize-none"
                      />
                    </div>

                    <div className="leather-stitch-box inline-block w-full sm:w-auto">
                      <button
                        id="rs-submit"
                        type="submit"
                        className="w-full sm:w-auto flex items-center justify-center gap-3 bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-semibold text-base px-10 py-4 rounded-xl transition-all duration-300 hover:shadow-[0_8px_30px_rgba(212,165,116,0.4)] active:scale-[0.98]"
                      >
                        Request Sample
                        <ArrowRight className="w-5 h-5" />
                      </button>
                    </div>

                    <p className="text-warm-beige/40 text-xs font-serif pt-1">
                      No sales pitch. We review every request personally and
                      respond within 24 hours.
                    </p>
                  </form>
                )}
              </div>
            </div>

            {/* 3-Step Sidebar */}
            <div className="lg:col-span-2 space-y-6">
              <div>
                <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
                  The Process
                </span>
                <h2 className="font-serif text-2xl sm:text-3xl text-warm-beige mt-2 mb-6">
                  From Brief to{" "}
                  <span className="text-saddle-tan">Bulk Production</span>
                </h2>
              </div>

              {STEPS.map((step, i) => (
                <div
                  key={step.step}
                  className="flex gap-5 p-5 rounded-xl border border-[#D4A574]/20 bg-[#2C1810]/50 hover:border-saddle-tan/40 transition-all duration-300 group"
                >
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-saddle-tan/10 border border-saddle-tan/40 flex items-center justify-center group-hover:bg-saddle-tan group-hover:border-saddle-tan transition-all duration-300">
                    <span className="font-serif text-saddle-tan group-hover:text-charcoal text-sm font-semibold transition-colors">
                      {step.step}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-serif text-warm-beige font-medium mb-1.5 group-hover:text-saddle-tan transition-colors">
                      {step.title}
                    </h3>
                    <p className="text-warm-beige/60 text-sm font-serif font-light leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}

              {/* Trust note */}
              <div className="mt-4 p-5 rounded-xl border border-[#D4A574]/15 bg-[#2C1810]/30">
                <p className="text-warm-beige/55 text-sm font-serif font-light leading-relaxed">
                  MOQ from <span className="text-saddle-tan">300 units</span>.
                  Bulk lead time{" "}
                  <span className="text-saddle-tan">45–60 days</span>. AQL 2.5
                  quality control. REACH & CA65 compliant.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
