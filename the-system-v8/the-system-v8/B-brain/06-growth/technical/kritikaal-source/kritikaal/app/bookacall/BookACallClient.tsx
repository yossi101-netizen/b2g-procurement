"use client";


import { BookACall as BookACallComponent } from "@/components/home/bookacall";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";

const BookACall = () => {
  const { t } = useTranslation();

  return (
    <>
      {/* Hero Section */}
      <section className="relative pt-24 sm:pt-32 pb-6 sm:pb-10 bg-charcoal overflow-hidden">
        {/* Leather background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
        </div>
        <div className="container mx-auto px-4 sm:px-6 relative z-10">
          <div className="max-w-3xl">
            <span className="text-saddle-tan font-medium tracking-widest uppercase text-xs sm:text-sm">
              {t('bookACallPage.badge')}
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl text-warm-beige mt-3 sm:mt-4 mb-4 sm:mb-6">
              <span className="text-warm-beige">{t('bookACallPage.title')}</span>{' '}
              <span className="text-saddle-tan">{t('bookACallPage.titleHighlight')}</span>
            </h1>
            <p className="text-base sm:text-lg text-warm-beige/80 leading-relaxed">
              {t('bookACallPage.description')}
            </p>
          </div>
        </div>
      </section>

      {/* Calendar Component */}
      <BookACallComponent />
    </>
  );
};

export default BookACall;
