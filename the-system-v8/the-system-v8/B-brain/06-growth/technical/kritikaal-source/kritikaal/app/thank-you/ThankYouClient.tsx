"use client";


import Link from "next/link";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { CheckCircle, Mail, ArrowLeft, Home, FileText } from "lucide-react";
import { useTranslation } from "@/contexts/TranslationContext";

const ThankYou = () => {
  const { t } = useTranslation();

  return (
    <>
      <section className="relative py-24 sm:py-24 md:py-40 bg-gradient-to-br from-warm-beige via-warm-beige to-saddle-tan/10 min-h-screen flex items-center">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 1, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="bg-white rounded-2xl shadow-2xl p-8 sm:p-12 md:p-16 text-center"
            >
              {/* Success Icon */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                className="flex justify-center mb-6"
              >
                <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-12 h-12 sm:w-14 sm:h-14 text-green-600" />
                </div>
              </motion.div>

              {/* Thank You Message */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl text-charcoal mb-4">
                  {t('thankYouPage.title')}
                </h1>
                <p className="text-lg sm:text-xl text-charcoal/70 mb-8">
                  {t('thankYouPage.subtitle')}
                </p>
              </motion.div>

              {/* Email Notification Info */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-saddle-tan/5 border border-saddle-tan/20 rounded-xl p-6 mb-8"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-full bg-saddle-tan/10 flex items-center justify-center flex-shrink-0">
                    <Mail className="w-6 h-6 text-saddle-tan" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-serif text-lg font-semibold text-charcoal mb-2">
                      {t('thankYouPage.checkEmailTitle')}
                    </h3>
                    <p className="text-charcoal/70 text-sm sm:text-base">
                      {t('thankYouPage.checkEmailDesc')}
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* What's Next Section */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="border-t border-charcoal/10 pt-8 mb-8"
              >
                <h3 className="font-serif text-xl text-charcoal mb-4">{t('thankYouPage.whatsNext')}</h3>
                <div className="grid sm:grid-cols-2 gap-4 text-left">
                  <div className="bg-warm-beige/30 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <FileText className="w-5 h-5 text-saddle-tan" />
                      <h4 className="font-semibold text-charcoal">{t('thankYouPage.step1Title')}</h4>
                    </div>
                    <p className="text-sm text-charcoal/70">
                      {t('thankYouPage.step1Desc')}
                    </p>
                  </div>
                  <div className="bg-warm-beige/30 rounded-lg p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <Mail className="w-5 h-5 text-saddle-tan" />
                      <h4 className="font-semibold text-charcoal">{t('thankYouPage.step2Title')}</h4>
                    </div>
                    <p className="text-sm text-charcoal/70">
                      {t('thankYouPage.step2Desc')}
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Action Buttons */}
              <motion.div
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="flex flex-col sm:flex-row gap-4 justify-center"
              >
                <Link href="/">
                  <Button 
                    className="bg-saddle-tan hover:bg-saddle-tan/90 text-white font-normal"
                    size="lg"
                  >
                    <Home className="w-5 h-5 mr-2" />
                    {t('thankYouPage.backHome')}
                  </Button>
                </Link>
                <Link href="/bookacall">
                  <Button 
                    variant="outline"
                    className="border-saddle-tan text-saddle-tan hover:bg-saddle-tan/10"
                    size="lg"
                  >
                    <Mail className="w-5 h-5 mr-2" />
                    {t('thankYouPage.bookConsultation')}
                  </Button>
                </Link>
              </motion.div>

              {/* Additional Note */}
              <motion.p
                initial={{ opacity: 1 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7 }}
                className="text-xs sm:text-sm text-charcoal/50 mt-8"
              >
                {t('thankYouPage.needHelp')}{" "}
                <a href="mailto:info@KRITIKAAL.com" className="text-saddle-tan hover:underline">
                  info@KRITIKAAL.com
                </a>
              </motion.p>
            </motion.div>
          </div>
        </div>
      </section>
    </>
  );
};

export default ThankYou;

