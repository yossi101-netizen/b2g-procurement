"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mail, MapPin, Linkedin, Instagram, Youtube, MessageCircle } from "lucide-react";
import { FaWhatsapp } from "react-icons/fa";
import { useTranslation } from "@/contexts/TranslationContext";
import { Link as ScrollLink } from 'react-scroll';

export const Footer = () => {
  const { t } = useTranslation();
  const pathname = usePathname();

  const footerLinks = {
    company: [
      { name: t('footer.companyWhyKRITIKAAL'), path: "/why-KRITIKAAL" },
      { name: t('footer.companyWhyIndia'), path: "/why-india" },
      { name: t('footer.companyHowItWorks'), path: "/how-it-works" },
      { name: t('footer.companyProducts'), path: "/products" },
      { name: "FAQ", path: "/faq" },
      { name: "Blog", path: "/blog" },
    ],
    products: [
      { name: t('footer.productsBelts'), path: "/products" },
      { name: t('footer.productsBags'), path: "/products" },
      { name: t('footer.productsWallets'), path: "/products" },
    ],
  };

  return (
    <footer className="relative overflow-hidden text-[#e6dccf]">
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

{/* Dark overlay */}
<div className="absolute inset-0 z-0 bg-black/60" />
      
      {/* Light overlay for lighter appearance */}
      <div
        className="absolute inset-0 z-[1]"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
        }}
      />
      
      {/* Dark overlay for text contrast */}
      <div
        className="absolute inset-0 z-[2]"
        style={{
          backgroundColor: 'rgba(44, 24, 16, 0.25)',
        }}
      />

      {/* Leather grain texture */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.08] z-[3]">
        <div className="absolute inset-0 
          bg-[radial-gradient(circle_at_1px_1px,#ffffff20_1px,transparent_0)] 
          bg-[length:7px_7px]" />
      </div>

      <div className="relative z-[4] container mx-auto px-4 py-8 md:py-12">
        
        {/* Mobile Layout */}
        <div className="block md:hidden">
          {/* Brand Title Only */}
          <div className="text-center mb-8">
            <h3 className="font-serif text-2xl font-medium tracking-wide mb-6">
              {t('footer.brandTitle')}
            </h3>
            
            {/* Contact Details */}
            <div className="space-y-4">
              <a 
                href="mailto:contact@KRITIKAAL.com" 
                className="flex items-center justify-center gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
              >
                <Mail className="w-4 h-4 text-[#D4A574] group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                <span className="group-hover:scale-105 transition-transform duration-300">contact@KRITIKAAL.com</span>
              </a>
              <a 
                href="https://wa.me/919187662604" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
              >
                <FaWhatsapp className="w-4 h-4 text-[#D4A574] group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                <span className="group-hover:scale-105 transition-transform duration-300">+91 9187662604</span>
              </a>
              <a 
                href="https://maps.google.com/?q=Bengaluru,Karnataka,India" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
              >
                <MapPin className="w-4 h-4 text-[#D4A574] group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                <span className="group-hover:scale-105 transition-transform duration-300">{t('footer.location')}</span>
              </a>
            </div>
          </div>
        </div>

        {/* Desktop Layout */}
        <div className="hidden md:grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8 md:gap-14">

          {/* Brand */}
          <div className="lg:col-span-2 text-center sm:text-left">
            {pathname === '/' ? (
              <ScrollLink
                to="hero"
                smooth={true}
                duration={500}
                className="cursor-pointer"
              >
                <h3 className="font-serif text-2xl md:text-3xl font-medium tracking-wide mb-4 md:mb-5">
                  {t('footer.brandTitle')}
                </h3>
              </ScrollLink>
            ) : (
              <Link href="/" className="cursor-pointer">
                <h3 className="font-serif text-2xl md:text-3xl font-medium tracking-wide mb-4 md:mb-5">
                  {t('footer.brandTitle')}
                </h3>
              </Link>
            )}
            <p className="text-[#cfc2b3] max-w-sm leading-relaxed mb-5 md:mb-7 mx-auto sm:mx-0">
              {t('footer.brandDescription')}
            </p>

            {/* Social */}
            <div className="flex gap-4 justify-center sm:justify-start">
              {[
                { Icon: Linkedin, link: "https://www.linkedin.com/company/KRITIKAAL/?viewAsMember=true" },
                { Icon: Instagram, link: "https://www.instagram.com" },
                { Icon: Youtube, link: "https://www.youtube.com" },
              ].map(({ Icon, link }, i) => (
                <a
                  key={i}
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-11 h-11 rounded-full 
                    bg-[#2e1f16] border border-[#3a2a1f]
                    flex items-center justify-center
                    hover:bg-[#3b291d] hover:border-[#D4A574]/40
                    hover:shadow-[0_0_12px_rgba(212,165,116,0.3)]
                    hover:scale-110
                    transition-all duration-300"
                >
                  <Icon className="w-5 h-5 text-[#F5E6D3]/80 group-hover:text-white transition-colors duration-300" />
                </a>
              ))}
            </div>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-serif font-light mb-4 tracking-wide">{t('footer.companyTitle')}</h4>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.path}
                    prefetch={true}
                    className={`
                      transition-colors duration-300 
                      hover:text-[#F5E6D3] 
                      relative
                      group
                      ${pathname === link.path 
                        ? 'text-white font-semibold' 
                        : 'text-[#F5E6D3]/80'
                      }
                    `}
                  >
                    <span className="relative">
                      {link.name}
                      <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-[#D4A574] group-hover:w-full transition-all duration-300" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Products */}
          <div>
            <h4 className="font-serif font-light mb-4 tracking-wide">{t('footer.productsTitle')}</h4>
            <ul className="space-y-3">
              {footerLinks.products.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.path}
                    prefetch={true}
                    className={`
                      transition-colors duration-300 
                      hover:text-[#F5E6D3] 
                      relative
                      group
                      ${pathname === link.path 
                        ? 'text-white font-semibold' 
                        : 'text-[#F5E6D3]/80'
                      }
                    `}
                  >
                    <span className="relative">
                      {link.name}
                      <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-[#D4A574] group-hover:w-full transition-all duration-300" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-serif font-light mb-4 tracking-wide">{t('footer.contactTitle')}</h4>
            <ul className="space-y-4">
              <li>
                <a 
                  href="mailto:contact@KRITIKAAL.com" 
                  className="flex items-center gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
                >
                  <Mail className="w-4 h-4 text-[#D4A574] group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                  <span className="group-hover:translate-x-0.5 transition-transform duration-300">contact@KRITIKAAL.com</span>
                </a>
              </li>
              <li>
                <a 
                  href="https://wa.me/919187662604" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
                >
                  <FaWhatsapp className="w-4 h-4 text-[#D4A574] group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                  <span className="group-hover:translate-x-0.5 transition-transform duration-300">+91 9187662604</span>
                </a>
              </li>
              <li>
                <a 
                  href="https://maps.google.com/?q=Bengaluru,Karnataka,India" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-start gap-3 text-[#F5E6D3]/80 hover:text-[#F5E6D3] transition-all duration-300 group"
                >
                  <MapPin className="w-4 h-4 text-[#D4A574] mt-1 group-hover:text-[#D4A574] group-hover:drop-shadow-[0_0_8px_rgba(212,165,116,0.5)] transition-all duration-300" />
                  <span className="group-hover:translate-x-0.5 transition-transform duration-300">{t('footer.location')}</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="border-t border-[#3a2a1f] mt-14 pt-8 
          flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-[#b8aa9a] text-sm">
            {t('footer.copyright')}
          </p>
          <div className="flex gap-6 text-sm">
            <Link 
              href="#" 
              className="text-[#F5E6D3]/70 hover:text-[#F5E6D3] transition-colors duration-300 relative group"
            >
              <span className="relative">
                {t('footer.privacyPolicy')}
                <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-[#D4A574]/50 group-hover:w-full transition-all duration-300" />
              </span>
            </Link>
            <Link 
              href="#" 
              className="text-[#F5E6D3]/70 hover:text-[#F5E6D3] transition-colors duration-300 relative group"
            >
              <span className="relative">
                {t('footer.termsOfService')}
                <span className="absolute bottom-0 left-0 w-0 h-[1px] bg-[#D4A574]/50 group-hover:w-full transition-all duration-300" />
              </span>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

