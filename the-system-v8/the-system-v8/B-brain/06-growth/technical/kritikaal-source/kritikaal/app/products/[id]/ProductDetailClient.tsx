"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, Phone, Package, Ruler, Shield, Clock } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "@/contexts/TranslationContext";

interface Product {
  id: number;
  name: string;
  variant: string;
  image: string;
  description: string;
  material: string;
  useCases: string[];
  manufacturingHighlights: string[];
  moqOptions: { quantity: string; description: string }[];
}

export default function ProductDetailClient({ product }: { product: Product }) {
  const { t } = useTranslation();
  const router = useRouter();
  const [selectedMOQ, setSelectedMOQ] = useState<string | null>(null);

  return (
    <>
      {/* Back Navigation */}
      <section className="bg-background pt-24 pb-4">
        <div className="container mx-auto px-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('productDetailPage.backToProducts')}
          </button>
        </div>
      </section>

      {/* Product Detail */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Product Image */}
            <motion.div
              initial={{ opacity: 1, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="relative"
            >
              <div className="bg-warm-beige rounded-2xl p-8 aspect-square flex items-center justify-center">
                <img
                  src={product.image}
                  alt={`${product.name} - ${product.variant}`}
                  className="max-w-[80%] max-h-[80%] object-contain"
                  style={{
                    filter: 'drop-shadow(0 25px 25px rgba(0,0,0,0.25))',
                  }}
                />
              </div>
            </motion.div>

            {/* Product Info */}
            <motion.div
              initial={{ opacity: 1, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8"
            >
              {/* Header */}
              <div>
                <span className="text-saddle-tan font-medium tracking-widest uppercase text-sm">
                  {product.variant} {t('productDetailPage.variantLabel')}
                </span>
                <h1 className="font-serif text-4xl md:text-5xl text-foreground mt-2 mb-4">
                  {product.name}
                </h1>
                <p className="text-muted-foreground text-lg leading-relaxed">
                  {product.description}
                </p>
              </div>

              {/* Material & Specs */}
              <div className="bg-card rounded-xl p-6 space-y-4">
                <div className="flex items-start gap-3">
                  <Ruler className="w-5 h-5 text-saddle-tan mt-1" />
                  <div>
                    <h3 className="font-serif font-light text-foreground mb-1">{t('productDetailPage.materialLabel')}</h3>
                    <p className="text-muted-foreground text-sm">{product.material}</p>
                  </div>
                </div>
              </div>

              {/* Use Cases */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Package className="w-5 h-5 text-saddle-tan" />
                  <h3 className="font-serif font-light text-foreground">{t('productDetailPage.idealForLabel')}</h3>
                </div>
                <ul className="grid grid-cols-2 gap-2">
                  {product.useCases.map((useCase, index) => (
                    <li key={index} className="flex items-center gap-2 text-muted-foreground text-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-saddle-tan" />
                      {useCase}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Manufacturing Highlights */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-5 h-5 text-saddle-tan" />
                  <h3 className="font-serif font-light text-foreground">{t('productDetailPage.manufacturingLabel')}</h3>
                </div>
                <ul className="space-y-2">
                  {product.manufacturingHighlights.map((highlight, index) => (
                    <li key={index} className="flex items-center gap-2 text-muted-foreground text-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-saddle-tan" />
                      {highlight}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* MOQ Selection & CTA */}
      <section className="py-24 bg-card">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 1, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl mx-auto"
          >
            <div className="text-center mb-8">
              <div className="flex items-center justify-center gap-2 mb-3">
                <Clock className="w-5 h-5 text-saddle-tan" />
                <h2 className="font-serif text-2xl md:text-3xl text-foreground">
                  {t('productDetailPage.moqTitle')}
                </h2>
              </div>
              <p className="text-muted-foreground">
                {t('productDetailPage.moqSubtitle')}
              </p>
            </div>

            {/* MOQ Options */}
            <div className="grid md:grid-cols-2 gap-4 mb-10">
              {product.moqOptions.map((option, index) => (
                <motion.button
                  key={option.quantity}
                  initial={{ opacity: 1, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.1 }}
                  onClick={() => setSelectedMOQ(option.quantity)}
                  className={`p-6 rounded-xl border-2 transition-all duration-300 text-left ${
                    selectedMOQ === option.quantity
                      ? "border-saddle-tan bg-saddle-tan/10"
                      : "border-border hover:border-saddle-tan/50 bg-background"
                  }`}
                >
                  <div className="font-serif text-2xl text-foreground mb-2">
                    {option.quantity}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                </motion.button>
              ))}
            </div>

            {/* CTA Section */}
            <div className="bg-charcoal rounded-2xl p-8 text-center">
              <h3 className="font-serif text-2xl text-warm-beige mb-3">
                {t('productDetailPage.ctaTitle')}
              </h3>
              <p className="text-warm-beige/70 mb-6 max-w-lg mx-auto">
                {t('productDetailPage.ctaSubtitle')}
              </p>
              <div className="leather-stitch-box inline-block">
                <Link href="/bookacall">
                  <Button 
                    size="lg" 
                    className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal"
                  >
                    <Phone className="w-5 h-5 mr-2" />
                    {t('productDetailPage.ctaButton')}
                    {selectedMOQ && ` — ${selectedMOQ}`}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              </div>
              <p className="text-warm-beige/50 text-sm mt-4">
                {t('productDetailPage.ctaFooter')}
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
}
