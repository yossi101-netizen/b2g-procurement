"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Menu, X, ChevronDown, HelpCircle, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "@/contexts/TranslationContext";
import { navigateToSection } from "@/utils/navigation";


export const Navbar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showNavbar, setShowNavbar] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [homeDropdownOpen, setHomeDropdownOpen] = useState(false);
  const [mobileHomeExpanded, setMobileHomeExpanded] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useTranslation();

  // Returns true when this nav link's page is the active route
  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname === path || pathname.startsWith(path + "/");
  };

  const homeDropdownLinks = [
    {
      name: "FAQ",
      path: "/faq",
      icon: HelpCircle,
      desc: "29 answers on MOQ, compliance & lead times",
    },
    {
      name: "Blog",
      path: "/blog",
      icon: BookOpen,
      desc: "Expert articles on leather manufacturing",
    },
  ];

  const navLinks = [
    { name: t('nav.home'), path: "/", sectionId: "hero", hasDropdown: true },
    { name: t('nav.whyKRITIKAAL'), path: "/why-KRITIKAAL" },
    { name: t('nav.whyIndia'), path: "/why-india" },
    { name: t('nav.howItWorks'), path: "/how-it-works" },
    { name: t('nav.products'), path: "/products" },
    { name: "Calculator", path: "/calculator" },
  ];

  // Handle navigation click
  const handleNavClick = (e: React.MouseEvent, link: typeof navLinks[0]) => {
    if (link.sectionId) {
      e.preventDefault();
      navigateToSection((path: string) => router.push(path), pathname, link.sectionId);
      setIsMobileMenuOpen(false);
    }
  };

  // Handle logo click
  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigateToSection((path: string) => router.push(path), pathname, "hero");
  };

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  useEffect(() => {
    document.body.style.background =
      "radial-gradient(circle at top, #4A3228 0%, #3E2723 35%, #2C1810 70%, #1A0F0A 100%)";
    document.body.style.minHeight = "100vh";
  }, []);

  // Add/remove class to body when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.classList.add('mobile-menu-open');
    } else {
      document.body.classList.remove('mobile-menu-open');
    }
    
    return () => {
      document.body.classList.remove('mobile-menu-open');
    };
  }, [isMobileMenuOpen]);

  // Handle navbar visibility on scroll
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const currentScrollY = window.scrollY;

          // Always show navbar when at the top
          if (currentScrollY < 100) {
            setShowNavbar(true);
          }
          // Show navbar when scrolling up
          else if (currentScrollY < lastScrollY) {
            setShowNavbar(true);
          }
          // Hide navbar when scrolling down
          else if (currentScrollY > lastScrollY && currentScrollY > 100) {
            setShowNavbar(false);
          }

          setLastScrollY(currentScrollY);
          ticking = false;
        });

        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [lastScrollY]);

  return (
    <motion.nav
      initial={{ opacity: 1, y: -20 }}
      animate={{ 
        opacity: 1, 
        y: showNavbar ? 0 : -200,
        transition: {
          duration: 0.3,
          ease: "easeInOut"
        }
      }}
      className="fixed top-0 left-0 right-0 z-50 h-32 md:h-36 lg:h-[160px]"
      style={{
        willChange: 'transform'
      }}
    >
      {/* Leather texture background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: 'url("/leather-navbar.png")',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          imageRendering: 'crisp-edges',
        }}
      />
      
      {/* Dark overlay for text readability */}
      <div
        className="absolute inset-0 z-[1]"
        style={{
          backgroundColor: 'rgba(44, 24, 16, 0.35)',
        }}
      />
      
         {/* Stitch borders */}
<div
  className="absolute top-1 left-2 right-2 md:left-4 md:right-4 h-[2px] pointer-events-none z-20"
  style={{
    backgroundImage:
      "repeating-linear-gradient(90deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
    opacity: 0.85,
  }}
/>

<div
  className="absolute bottom-1 left-2 right-2 md:left-4 md:right-4 h-[2px] pointer-events-none z-20"
  style={{
    backgroundImage:
      "repeating-linear-gradient(90deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
    opacity: 0.85,
  }}
/>

<div
  className="absolute top-3 bottom-3 left-1 w-[2px] pointer-events-none z-20"
  style={{
    backgroundImage:
      "repeating-linear-gradient(180deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
    opacity: 0.85,
  }}
/>

<div
  className="absolute top-3 bottom-3 right-1 w-[2px] pointer-events-none z-20"
  style={{
    backgroundImage:
      "repeating-linear-gradient(180deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
    opacity: 0.85,
  }}
/>

      {/* Enhanced grain texture for depth */}
      <div
        className="absolute inset-0 pointer-events-none z-[2]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          opacity: 0.06,
          mixBlendMode: "overlay",
        }}
      />

      <div className="container mx-auto px-4 md:px-6 relative z-30 h-full flex items-center">
        <div className="flex items-center justify-between w-full relative">

          {/* LOGO + TAGLINE */}
<a
  href="/"
  onClick={handleLogoClick}
  className="flex items-center gap-3 cursor-pointer"
>
  <motion.img
    src="/KRITIKAAL Logo.png"
    alt="KRITIKAAL Logo"
    className="w-auto h-20 sm:h-24 md:h-28 lg:h-32 xl:h-36"
    whileHover={{ scale: 1.05 }}
    transition={{ type: "spring", stiffness: 230, damping: 18 }}
    style={{
      filter:
        "drop-shadow(0 6px 18px rgba(0,0,0,0.7)) drop-shadow(0 0 14px rgba(245,230,211,0.4))",
      maxWidth: "620px",
    }}
  />

  {/* STACKED TEXT */}
  <div className="flex flex-col justify-end pb-1">
    <motion.div
      initial={{ opacity: 1, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.15 }}
      className="font-allura tracking-wide text-sm sm:text-base md:text-lg lg:text-xl mt-4 sm:mt-5 md:mt-6"
      style={{ color: "#F5E6D3" }}
    >
      <span>{t('tagline.yourCraft')}</span>
      <span className="mx-2">-</span>
      <span>{t('tagline.ourResponsibility')}</span>
    </motion.div>
  </div>
</a>

          {/* DESKTOP NAV */}
          <div className="hidden lg:flex font-serif items-center gap-8">
            {navLinks.map((link) => (
              link.hasDropdown ? (
                // Home with dropdown
                <div
                  key={link.path}
                  className="relative"
                  ref={dropdownRef}
                  onMouseEnter={() => setHomeDropdownOpen(true)}
                  onMouseLeave={() => setHomeDropdownOpen(false)}
                >
                  <a
                    href={link.path}
                    onClick={(e) => handleNavClick(e, link)}
                    className={`flex items-center gap-1 text-base font-medium transition-colors duration-300 hover:text-[#D4A574] cursor-pointer relative group ${
                      isActive(link.path) ? "text-[#D4A574]" : "text-[#F5E6D3]/90"
                    }`}
                  >
                    {link.name}
                    <ChevronDown
                      className={`w-3.5 h-3.5 mt-0.5 transition-transform duration-300 ${
                        homeDropdownOpen ? "rotate-180 text-[#D4A574]" : ""
                      }`}
                    />
                    <span
                      className={`absolute -bottom-1 left-0 h-[2px] bg-[#D4A574] transition-all duration-300 ${
                        isActive(link.path) ? "w-full" : "w-0 group-hover:w-full"
                      }`}
                    />
                  </a>

                  {/* Dropdown panel */}
                  <AnimatePresence>
                    {homeDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 8 }}
                        transition={{ duration: 0.2, ease: "easeOut" }}
                        className="absolute top-full left-0 mt-3 w-64 z-[60]"
                      >
                        {/* Arrow pointer */}
                        <div className="absolute -top-1.5 left-4 w-3 h-3 bg-[#2C1810] border-l border-t border-[#D4A574]/30 rotate-45" />
                        <div
                          className="rounded-xl overflow-hidden shadow-2xl border border-[#D4A574]/25"
                          style={{
                            background: "linear-gradient(135deg, #1A0F0A 0%, #2C1810 100%)",
                          }}
                        >
                          {homeDropdownLinks.map((item, i) => {
                            const Icon = item.icon;
                            return (
                              <Link
                                key={item.path}
                                href={item.path}
                                prefetch={true}
                                onClick={() => setHomeDropdownOpen(false)}
                                className={`flex items-start gap-3 px-4 py-3.5 group/item hover:bg-[#D4A574]/10 transition-all duration-200 ${
                                  i > 0 ? "border-t border-[#D4A574]/10" : ""
                                }`}
                              >
                                <div className="shrink-0 w-8 h-8 rounded-lg bg-[#D4A574]/15 flex items-center justify-center group-hover/item:bg-[#D4A574]/25 transition-colors duration-200">
                                  <Icon className="w-4 h-4 text-[#D4A574]" />
                                </div>
                                <div>
                                  <p className="font-serif font-medium text-[#F5E6D3] group-hover/item:text-[#D4A574] transition-colors duration-200 text-sm">
                                    {item.name}
                                  </p>
                                  <p className="text-[#F5E6D3]/50 text-xs mt-0.5 font-sans font-light leading-relaxed">
                                    {item.desc}
                                  </p>
                                </div>
                              </Link>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ) : link.sectionId ? (
                <a
                  key={link.path}
                  href={link.path}
                  onClick={(e) => handleNavClick(e, link)}
                  className={`text-base font-medium transition-colors duration-300 hover:text-[#D4A574] cursor-pointer relative group ${
                    pathname === link.path ? "text-[#D4A574]" : "text-[#F5E6D3]/90"
                  }`}
                >
                  {link.name}
                  <span
                    className={`absolute -bottom-1 left-0 h-[2px] bg-[#D4A574] transition-all duration-300 ${
                      pathname === link.path ? "w-full" : "w-0 group-hover:w-full"
                    }`}
                  />
                </a>
              ) : (
                <Link
                  key={link.path}
                  href={link.path}
                  prefetch={true}
                  className={`text-base font-medium transition-colors duration-300 hover:text-[#D4A574] relative group ${
                    isActive(link.path) ? "text-[#D4A574]" : "text-[#F5E6D3]/90"
                  }`}
                >
                  {link.name}
                  <span
                    className={`absolute -bottom-1 left-0 h-[2px] bg-[#D4A574] transition-all duration-300 ${
                      isActive(link.path) ? "w-full" : "w-0 group-hover:w-full"
                    }`}
                  />
                </Link>
              )
            ))}
          </div>

          {/* CTA */}
          <div className="hidden lg:flex items-center gap-4">
            <div className="leather-stitch-box inline-block">
              <Link href="/bookacall">
                <Button
                  variant="cta"
                  size="xl"
                  className="bg-[#D4A574] hover:bg-[#C49464] text-white text-lg font-serif font-semibold px-8 py-4"
                >
                  {t('nav.bookACall')}
                </Button>
              </Link>
            </div>
          </div>

          {/* MOBILE MENU BUTTON */}
          <button
  className="lg:hidden p-3 relative z-50"
  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
  aria-label="Toggle menu"
>
  {isMobileMenuOpen ? (
    <X className="w-8 h-8 text-[#F5E6D3]" />
  ) : (
    <Menu className="w-8 h-8 text-[#F5E6D3]" />
  )}
</button>
        </div>
      </div>

      {/* MOBILE MENU DROPDOWN */}
<AnimatePresence>
  {isMobileMenuOpen && (
    <motion.div
      initial={{ opacity: 1, y: -25 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -25 }}
      transition={{ duration: 0.35, ease: "easeInOut" }}
      className="lg:hidden absolute top-full left-0 right-0 z-40 shadow-2xl min-h-[420px]"
    >
            {/* Leather texture background */}
            <div
              className="absolute inset-0 z-0"
              style={{
                backgroundImage: 'url("/leather-navbar.png")',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat',
              }}
            />
            
            {/* Solid dark overlay to prevent hero bleed-through */}
            <div
              className="absolute inset-0 z-[1]"
              style={{
                backgroundColor: 'rgba(30, 20, 15, 0.96)',
              }}
            />

            {/* Grain texture */}
            <div
              className="absolute inset-0 pointer-events-none z-[2]"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                opacity: 0.04,
                mixBlendMode: "overlay",
              }}
            />

            {/* Top stitch border */}
            <div
              className="absolute top-1 left-4 right-4 h-[2px] pointer-events-none z-[3]"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
                opacity: 0.7,
              }}
            />

            {/* Menu content */}
            <div className="relative z-[4] container mx-auto px-4 py-6">
              <div className="flex flex-col gap-1">
                {navLinks.map((link) => (
                  link.hasDropdown ? (
                    // Home expandable in mobile
                    <div key={link.path}>
                      <div className="flex items-center">
                        <a
                          href={link.path}
                          onClick={(e) => handleNavClick(e, link)}
                          className={`flex-1 py-3 px-4 text-base font-serif font-medium transition-all duration-200 rounded-md cursor-pointer ${
                            isActive(link.path)
                              ? "text-[#D4A574] bg-[#3E2723]/40"
                              : "text-[#F5E6D3]/90 hover:text-[#D4A574] hover:bg-[#3E2723]/30"
                          }`}
                        >
                          {link.name}
                        </a>
                        <button
                          onClick={() => setMobileHomeExpanded(!mobileHomeExpanded)}
                          className="p-3 text-[#D4A574] hover:bg-[#3E2723]/30 rounded-md transition-colors duration-200"
                          aria-label="Toggle home sub-menu"
                        >
                          <ChevronDown
                            className={`w-4 h-4 transition-transform duration-300 ${
                              mobileHomeExpanded ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                      </div>

                      {/* Sub-links */}
                      <AnimatePresence initial={false}>
                        {mobileHomeExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25 }}
                            style={{ overflow: "hidden" }}
                          >
                            <div className="ml-4 mt-1 space-y-1 border-l border-[#D4A574]/30 pl-4">
                              {homeDropdownLinks.map((item) => {
                                const Icon = item.icon;
                                return (
                                  <Link
                                    key={item.path}
                                    href={item.path}
                                    prefetch={true}
                                    onClick={() => {
                                      setIsMobileMenuOpen(false);
                                      setMobileHomeExpanded(false);
                                    }}
                                    className="flex items-center gap-3 py-2.5 px-3 rounded-md text-[#F5E6D3]/80 hover:text-[#D4A574] hover:bg-[#3E2723]/30 transition-all duration-200"
                                  >
                                    <Icon className="w-4 h-4 text-[#D4A574]/70 shrink-0" />
                                    <span className="font-serif text-sm font-medium">{item.name}</span>
                                  </Link>
                                );
                              })}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ) : link.sectionId ? (
                    <a
                      key={link.path}
                      href={link.path}
                      onClick={(e) => handleNavClick(e, link)}
                      className={`py-3 px-4 text-base font-serif font-medium transition-all duration-200 rounded-md cursor-pointer relative group ${
                        isActive(link.path)
                          ? "text-[#D4A574] bg-[#3E2723]/40"
                          : "text-[#F5E6D3]/90 hover:text-[#D4A574] hover:bg-[#3E2723]/30"
                      }`}
                    >
                      <span className="relative inline-block">
                        {link.name}
                        <span
                          className={`absolute -bottom-1 left-0 h-[2px] bg-[#D4A574] transition-all duration-300 ${
                            isActive(link.path) ? "w-full" : "w-0 group-hover:w-full"
                          }`}
                        />
                      </span>
                    </a>
                  ) : (
                    <Link
                      key={link.path}
                      href={link.path}
                      prefetch={true}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`py-3 px-4 text-base font-serif font-medium transition-all duration-200 rounded-md relative group ${
                        isActive(link.path)
                          ? "text-[#D4A574] bg-[#3E2723]/40"
                          : "text-[#F5E6D3]/90 hover:text-[#D4A574] hover:bg-[#3E2723]/30"
                      }`}
                    >
                      <span className="relative inline-block">
                        {link.name}
                        <span
                          className={`absolute -bottom-1 left-0 h-[2px] bg-[#D4A574] transition-all duration-300 ${
                            isActive(link.path) ? "w-full" : "w-0 group-hover:w-full"
                          }`}
                        />
                      </span>
                    </Link>
                  )
                ))}

                {/* Action Buttons */}
                <div className="mt-4 pt-4 border-t border-[#D4A574]/20 flex flex-col gap-3">
                  <Link
                    href="/bookacall"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="block w-full"
                  >
                    <Button
                      variant="cta"
                      className="w-full bg-[#D4A574] hover:bg-[#C49464] text-white font-serif font-semibold py-3 px-6 text-base shadow-lg"
                    >
                      {t('nav.bookACall')}
                    </Button>
                  </Link>
                </div>
              </div>
            </div>

            {/* Bottom stitch border */}
            <div
              className="absolute bottom-1 left-4 right-4 h-[2px] pointer-events-none z-[3]"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(90deg,#D4A574 0,#D4A574 7px,transparent 7px,transparent 13px)",
                opacity: 0.7,
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
};
