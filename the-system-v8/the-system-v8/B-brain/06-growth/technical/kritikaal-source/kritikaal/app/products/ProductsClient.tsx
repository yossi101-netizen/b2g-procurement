"use client";


import { motion, AnimatePresence, useMotionValue, useTransform } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useState, useEffect, useRef, useCallback } from "react";
import { ArrowRight, X } from "lucide-react";
import productsImage from "@/assets/products-showcase.jpg";
import leatherCraftsmanBg from "@/assets/leather-craftsman-1.jpg";
import { useTranslation } from "@/contexts/TranslationContext";

// Import Belt Sketches
import BraidedLeatherBelt from "@/assets/Sketches/Belts/Braided_Leather_Belt-removebg-preview.png";
import ClassicSquareBuckleBelt from "@/assets/Sketches/Belts/Classic_Square_Buckle_Belt-removebg-preview.png";
import FloralEmbossedBuckleBelt from "@/assets/Sketches/Belts/Floral_Embossed_Buckle_Belt-removebg-preview.png";
import HeavyStudRivetBelt from "@/assets/Sketches/Belts/Heavy_Stud_Rivet_Belt-removebg-preview.png";
import MinimalChainBelt from "@/assets/Sketches/Belts/Minimal_Chain_Belt-removebg-preview.png";
import MultiPocketUtilityBelt from "@/assets/Sketches/Belts/Multi-Pocket_Utility_Belt-removebg-preview.png";
import OrnateMedallionBuckleBelt from "@/assets/Sketches/Belts/Ornate_Medallion_Buckle_Belt-removebg-preview.png";
import SlimKnotBuckleBelt from "@/assets/Sketches/Belts/Slim_Knot_Buckle_Belt-removebg-preview.png";
import StuddedLeatherBelt from "@/assets/Sketches/Belts/Studded_Leather_Belt-removebg-preview.png";
import UtilityPocketBelt from "@/assets/Sketches/Belts/Utility_Pocket_Belt-removebg-preview.png";
import VintageRingBuckleBelt from "@/assets/Sketches/Belts/Vintage_Ring_Buckle_Belt-removebg-preview.png";
import WesternBullSkullBelt from "@/assets/Sketches/Belts/Western_Bull_Skull_Belt-removebg-preview.png";

// Import Bag Sketches
import DoubleBuckleBag from "@/assets/Sketches/Bags/Double_Buckle_Bag-removebg-preview.png";
import DuffelBag from "@/assets/Sketches/Bags/Duffel_Bag-removebg-preview.png";
import EmbossedTrunkBag from "@/assets/Sketches/Bags/Embossed_Trunk_Bag-removebg-preview.png";
import FlapShoulderBag from "@/assets/Sketches/Bags/Flap_Shoulder_Bag-removebg-preview.png";
import FlapTopBackpack from "@/assets/Sketches/Bags/Flap_Top_Backpack-removebg-preview.png";
import FringeFlapBag from "@/assets/Sketches/Bags/Fringe_Flap_Bag-removebg-preview.png";
import HoboShoulderBag from "@/assets/Sketches/Bags/Hogo_SHoulder_Bag-removebg-preview.png";
import MessengerBackpack from "@/assets/Sketches/Bags/Messenger_Backpack-removebg-preview.png";
import RoundTasselBag from "@/assets/Sketches/Bags/Round_Tessel_Bag-removebg-preview.png";
import Satchel from "@/assets/Sketches/Bags/Satchel-removebg-preview.png";

// Import Wallet Sketches
import BifoldWalletWithStrap from "@/assets/Sketches/Wallets/Bifold_Wallet_with_Strap-removebg-preview.png";
import ClassicBifoldWallet from "@/assets/Sketches/Wallets/Classic_Bifold_Wallet-removebg-preview.png";
import CoinPouchClaspClosure from "@/assets/Sketches/Wallets/Coin_Pouch__Clasp_Closure_-removebg-preview.png";
import EnvelopeWalletWithButtonLock from "@/assets/Sketches/Wallets/Envelope_Wallet_with_Button_Lock-removebg-preview.png";
import FlapWalletWithOrnamentalClasp from "@/assets/Sketches/Wallets/Flap_Wallet_with_Ornamental_Clasp-removebg-preview.png";
import PassportHolder from "@/assets/Sketches/Wallets/Passport_Holder-removebg-preview.png";
import SlimZipWallet from "@/assets/Sketches/Wallets/Slim_Zip_Wallet-removebg-preview.png";
import SmallFlapCoinWallet from "@/assets/Sketches/Wallets/Small_Flap_Coin_Wallet-removebg-preview.png";
import VerticalCardHolder from "@/assets/Sketches/Wallets/Vertical_Card_Holder-removebg-preview.png";
import ZipAroundCardWallet from "@/assets/Sketches/Wallets/Zip-Around_Card_Wallet-removebg-preview.png";
import ZipperPouchWallet from "@/assets/Sketches/Wallets/Zipper_Pouch_Wallet-removebg-preview.png";
import ZipWalletWithSnapStrap from "@/assets/Sketches/Wallets/Zip_Wallet_with_Snap_Strap-removebg-preview.png";

// Sketch Data Types
interface Sketch {
  id: string;
  name: string;
  image: any;
  description: string;
}

interface Category {
  id: string;
  title: string;
  sketches: Sketch[];
}

// Categories Data
const categoriesData: Category[] = [
  {
    id: "belts",
    title: "Belts",
    sketches: [
      { id: "belt-1", name: "Braided Leather Belt", image: BraidedLeatherBelt, description: "Intricately woven leather strips creating a flexible, elegant belt with timeless appeal" },
      { id: "belt-2", name: "Classic Square Buckle Belt", image: ClassicSquareBuckleBelt, description: "Traditional design with a clean square buckle, perfect for formal and casual wear" },
      { id: "belt-3", name: "Floral Embossed Buckle Belt", image: FloralEmbossedBuckleBelt, description: "Artistic floral patterns embossed on premium leather with decorative buckle" },
      { id: "belt-4", name: "Heavy Stud Rivet Belt", image: HeavyStudRivetBelt, description: "Bold statement piece with heavy-duty studs and rivets for edgy fashion" },
      { id: "belt-5", name: "Minimal Chain Belt", image: MinimalChainBelt, description: "Modern minimalist design featuring delicate chain accents" },
      { id: "belt-6", name: "Multi-Pocket Utility Belt", image: MultiPocketUtilityBelt, description: "Functional design with multiple pockets for practical everyday use" },
      { id: "belt-7", name: "Ornate Medallion Buckle Belt", image: OrnateMedallionBuckleBelt, description: "Luxurious belt featuring an ornate medallion-style buckle centerpiece" },
      { id: "belt-8", name: "Slim Knot Buckle Belt", image: SlimKnotBuckleBelt, description: "Sleek and sophisticated with an elegant knot-style buckle" },
      { id: "belt-9", name: "Studded Leather Belt", image: StuddedLeatherBelt, description: "Classic studded design for a rock-inspired aesthetic" },
      { id: "belt-10", name: "Utility Pocket Belt", image: UtilityPocketBelt, description: "Practical belt with integrated pocket for small essentials" },
      { id: "belt-11", name: "Vintage Ring Buckle Belt", image: VintageRingBuckleBelt, description: "Retro-inspired design with distinctive ring buckle closure" },
      { id: "belt-12", name: "Western Bull Skull Belt", image: WesternBullSkullBelt, description: "Western-style belt featuring iconic bull skull buckle design" },
    ],
  },
  {
    id: "bags",
    title: "Bags",
    sketches: [
      { id: "bag-1", name: "Double Buckle Bag", image: DoubleBuckleBag, description: "Structured bag with dual buckle closures for secure, stylish storage" },
      { id: "bag-2", name: "Duffel Bag", image: DuffelBag, description: "Spacious travel companion crafted from premium leather for weekend getaways" },
      { id: "bag-3", name: "Embossed Trunk Bag", image: EmbossedTrunkBag, description: "Vintage-inspired trunk style with beautiful embossed leather patterns" },
      { id: "bag-4", name: "Flap Shoulder Bag", image: FlapShoulderBag, description: "Elegant shoulder bag with protective flap closure and adjustable strap" },
      { id: "bag-5", name: "Flap Top Backpack", image: FlapTopBackpack, description: "Modern backpack design with classic flap top and leather accents" },
      { id: "bag-6", name: "Fringe Flap Bag", image: FringeFlapBag, description: "Bohemian-inspired bag featuring decorative leather fringe details" },
      { id: "bag-7", name: "Hobo Shoulder Bag", image: HoboShoulderBag, description: "Relaxed crescent-shaped bag for effortless everyday style" },
      { id: "bag-8", name: "Messenger Backpack", image: MessengerBackpack, description: "Versatile hybrid design combining messenger and backpack functionality" },
      { id: "bag-9", name: "Round Tassel Bag", image: RoundTasselBag, description: "Unique circular design adorned with playful tassel accents" },
      { id: "bag-10", name: "Satchel", image: Satchel, description: "Classic satchel design with structured silhouette and top handle" },
    ],
  },
  {
    id: "wallets",
    title: "Wallets / Accessories",
    sketches: [
      { id: "wallet-1", name: "Bifold Wallet with Strap", image: BifoldWalletWithStrap, description: "Classic bifold design with secure strap closure for added protection" },
      { id: "wallet-2", name: "Classic Bifold Wallet", image: ClassicBifoldWallet, description: "Timeless bifold wallet with multiple card slots and bill compartment" },
      { id: "wallet-3", name: "Coin Pouch (Clasp Closure)", image: CoinPouchClaspClosure, description: "Vintage-style coin pouch with elegant clasp closure mechanism" },
      { id: "wallet-4", name: "Envelope Wallet with Button Lock", image: EnvelopeWalletWithButtonLock, description: "Sleek envelope-style wallet with secure button lock closure" },
      { id: "wallet-5", name: "Flap Wallet with Ornamental Clasp", image: FlapWalletWithOrnamentalClasp, description: "Decorative wallet featuring ornate clasp and protective flap" },
      { id: "wallet-6", name: "Passport Holder", image: PassportHolder, description: "Travel essential designed to protect passport with additional card slots" },
      { id: "wallet-7", name: "Slim Zip Wallet", image: SlimZipWallet, description: "Minimalist design with zipper closure for secure compact storage" },
      { id: "wallet-8", name: "Small Flap Coin Wallet", image: SmallFlapCoinWallet, description: "Compact coin wallet with convenient flap closure" },
      { id: "wallet-9", name: "Vertical Card Holder", image: VerticalCardHolder, description: "Modern vertical design for easy card access and slim profile" },
      { id: "wallet-10", name: "Zip-Around Card Wallet", image: ZipAroundCardWallet, description: "Secure card wallet with full zip-around closure" },
      { id: "wallet-11", name: "Zipper Pouch Wallet", image: ZipperPouchWallet, description: "Versatile pouch-style wallet with zipper for mixed storage" },
      { id: "wallet-12", name: "Zip Wallet with Snap Strap", image: ZipWalletWithSnapStrap, description: "Dual security with zipper and snap strap closure" },
    ],
  },
];

// Premium 3D Flip Card Component with proper text orientation
interface Premium3DCardProps {
  sketch: Sketch;
  index: number;
  angle: number;
  x: number;
  z: number;
  isFocused: boolean;
  opacity: number;
  scale: number;
  onClickCard: (index: number) => void;
}

const Premium3DCard: React.FC<Premium3DCardProps> = ({
  sketch,
  index,
  angle,
  x,
  z,
  isFocused,
  opacity,
  scale,
  onClickCard,
}) => {
  const { t } = useTranslation();
  const [isFlipped, setIsFlipped] = useState(false);

  const handleHover = () => {
    setIsFlipped(true);
  };

  const handleHoverEnd = () => {
    setIsFlipped(false);
  };

  return (
    <motion.div
      className="absolute cursor-pointer"
      style={{
        transform: `translate3d(${x}px, 0, ${z}px) rotateY(${-angle}deg)`,
        transformStyle: "preserve-3d",
      }}
      onClick={() => onClickCard(index)}
      onMouseEnter={handleHover}
      onMouseLeave={handleHoverEnd}
    >
      {/* 3D Floating Card Container */}
      <motion.div
        className="relative"
        animate={{
          scale,
          y: isFocused ? -20 : [0, -8, 0],
          rotateX: isFocused ? 0 : 3,
        }}
        transition={{
          scale: { type: "spring", stiffness: 300, damping: 30 },
          y: isFocused 
            ? { type: "spring", stiffness: 300, damping: 30 }
            : { duration: 4, repeat: Infinity, ease: "easeInOut" },
          rotateX: { type: "spring", stiffness: 300, damping: 30 },
        }}
        style={{
          transformStyle: "preserve-3d",
          opacity,
        }}
      >
        {/* Card Flip Container */}
        <motion.div
          className="relative w-40 h-52 md:w-48 md:h-64"
          animate={{ rotateY: isFlipped ? 180 : 0 }}
          transition={{ 
            duration: 0.6, 
            ease: [0.23, 1, 0.32, 1],
          }}
          style={{
            transformStyle: "preserve-3d",
          }}
        >
          {/* FRONT FACE - Product Image */}
          <div
            className="absolute inset-0 rounded-2xl overflow-hidden"
            style={{
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
              background: isFocused 
                ? "linear-gradient(145deg, #FFF8F0 0%, #F5E6D3 50%, #E8DDD0 100%)"
                : "linear-gradient(145deg, #F5E6D3 0%, #E8DDD0 50%, #D4C4B0 100%)",
              boxShadow: isFocused
                ? `
                  0 30px 60px rgba(0,0,0,0.5),
                  0 0 40px rgba(212,165,116,0.3),
                  inset 0 2px 0 rgba(255,255,255,0.5)
                `
                : `
                  0 20px 40px rgba(0,0,0,0.35),
                  inset 0 1px 0 rgba(255,255,255,0.3)
                `,
              border: isFocused ? "3px solid #D4A574" : "2px solid #2C1810",
              transform: "translateZ(2px)",
            }}
          >
            {/* Product Image */}
            <div className="absolute inset-4 flex items-center justify-center">
              <motion.img
                src={sketch.image.src || sketch.image}
                alt={sketch.name}
                className="max-w-full max-h-full object-contain"
                style={{ 
                  filter: isFocused 
                    ? "drop-shadow(0 10px 20px rgba(0,0,0,0.35))"
                    : "drop-shadow(0 6px 12px rgba(0,0,0,0.25))",
                }}
                animate={isFocused ? { 
                  scale: [1, 1.03, 1],
                  y: [0, -3, 0],
                } : {}}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
            </div>

            {/* Shimmer effect */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              animate={{
                background: [
                  "linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)",
                  "linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.2) 50%, transparent 70%)",
                  "linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)",
                ],
              }}
              transition={{ duration: 3, repeat: Infinity }}
            />

            {/* Glow effect on focus */}
            {isFocused && (
              <motion.div
                className="absolute inset-0 pointer-events-none"
                initial={{ opacity: 1 }}
                animate={{ opacity: [0.2, 0.4, 0.2] }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{
                  background: "radial-gradient(circle at center, rgba(212,165,116,0.25) 0%, transparent 60%)",
                }}
              />
            )}

            {/* Product Name Overlay - Always Readable on Front */}
            <div
              className="absolute bottom-0 left-0 right-0 p-3"
              style={{
                background: "linear-gradient(0deg, rgba(44,24,16,0.95) 0%, rgba(44,24,16,0.7) 60%, transparent 100%)",
              }}
            >
              <p 
                className="text-white text-sm font-serif font-normal text-center truncate"
                style={{
                  textShadow: "0 2px 4px rgba(0,0,0,0.5)",
                }}
              >
                {sketch.name}
              </p>
              <p className="text-[#D4A574] text-xs text-center mt-1 opacity-80">
                {t('productsPage.hoverForDetails')}
              </p>
            </div>
          </div>

          {/* BACK FACE - Product Image with Details Overlay (Counter-rotated for correct text orientation) */}
          <div
            className="absolute inset-0 rounded-2xl overflow-hidden"
            style={{
              backfaceVisibility: "hidden",
              WebkitBackfaceVisibility: "hidden",
              transform: "rotateY(180deg) translateZ(2px)",
              background: isFocused 
                ? "linear-gradient(145deg, #FFF8F0 0%, #F5E6D3 50%, #E8DDD0 100%)"
                : "linear-gradient(145deg, #F5E6D3 0%, #E8DDD0 50%, #D4C4B0 100%)",
              boxShadow: `
                0 30px 60px rgba(0,0,0,0.5),
                0 0 30px rgba(212,165,116,0.2),
                inset 0 1px 0 rgba(255,255,255,0.3)
              `,
              border: "2px solid #D4A574",
            }}
          >
            {/* Product Image on Back */}
            <div className="absolute inset-4 flex items-center justify-center">
              <motion.img
                src={sketch.image.src || sketch.image}
                alt={sketch.name}
                className="max-w-full max-h-full object-contain opacity-40"
                style={{ 
                  filter: "drop-shadow(0 6px 12px rgba(0,0,0,0.2))",
                }}
              />
            </div>

            {/* Dark overlay for text readability */}
            <div 
              className="absolute inset-0"
              style={{
                background: "linear-gradient(180deg, rgba(44,24,16,0.85) 0%, rgba(26,15,10,0.9) 50%, rgba(44,24,16,0.95) 100%)",
              }}
            />

            {/* Decorative top pattern */}
            <div 
              className="absolute top-0 left-0 right-0 h-1.5 z-10"
              style={{
                background: "linear-gradient(90deg, #D4A574 0%, #8B6914 50%, #D4A574 100%)",
              }}
            />

            {/* Back Content - Product Details */}
            <div className="absolute inset-0 flex flex-col p-4 pt-5 z-10">
              {/* Product Name - Large and Clear */}
              <motion.h3 
                className="text-white font-serif text-base md:text-lg font-medium text-center mb-2 leading-tight"
                initial={{ opacity: 1, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                style={{
                  textShadow: "0 2px 8px rgba(0,0,0,0.5)",
                }}
              >
                {sketch.name}
              </motion.h3>

              {/* Decorative divider */}
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-6 h-[1px] bg-gradient-to-r from-transparent to-[#D4A574]" />
                <div className="w-1.5 h-1.5 rounded-full bg-[#D4A574]" />
                <div className="w-6 h-[1px] bg-gradient-to-l from-transparent to-[#D4A574]" />
              </div>

              {/* Description */}
              <motion.p 
                className="text-warm-beige/90 text-[11px] leading-relaxed text-center flex-1 overflow-hidden"
                initial={{ opacity: 1 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                style={{
                  display: "-webkit-box",
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: "vertical",
                  textShadow: "0 1px 2px rgba(0,0,0,0.3)",
                }}
              >
                {sketch.description}
              </motion.p>

              {/* Unit Selection Preview */}
              <motion.div 
                className="mt-auto pt-2"
                initial={{ opacity: 1, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <p className="text-[#D4A574] text-[9px] text-center uppercase tracking-wider mb-1.5">
                  {t('productsPage.minOrderQty')}
                </p>
                <div className="flex justify-center gap-2">
                  <span className="px-2 py-1 rounded bg-[#D4A574]/25 text-[#D4A574] text-[10px] font-serif font-medium border border-[#D4A574]/30">
                    300 {t('productsPage.units')}
                  </span>
                  <span className="px-2 py-1 rounded bg-[#D4A574]/25 text-[#D4A574] text-[10px] font-serif font-medium border border-[#D4A574]/30">
                    500 {t('productsPage.units')}
                  </span>
                </div>
              </motion.div>

              {/* CTA */}
              <motion.div
                className="mt-2 text-center"
                initial={{ opacity: 1 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                <span 
                  className="inline-flex items-center gap-1 text-[#2C1810] text-[10px] font-serif font-normal px-3 py-1.5 rounded-full"
                  style={{
                    background: "linear-gradient(135deg, #D4A574 0%, #C49464 100%)",
                    boxShadow: "0 4px 12px rgba(212,165,116,0.4)",
                  }}
                >
                  {t('productsPage.clickToBook')}
                  <ArrowRight className="w-3 h-3" />
                </span>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* 3D Shadow underneath */}
        <motion.div
          className="absolute -bottom-5 left-1/2 -translate-x-1/2 w-[85%] h-5 rounded-full"
          animate={{
            scale: isFlipped ? 1.1 : (isFocused ? 1.2 : 1),
            opacity: isFlipped ? 0.5 : 0.4,
          }}
          style={{
            background: "radial-gradient(ellipse, rgba(0,0,0,0.5) 0%, transparent 70%)",
            filter: "blur(6px)",
            transform: "translateZ(-30px)",
          }}
        />

        {/* Floating particles effect for focused card */}
        {isFocused && (
          <>
            {[...Array(4)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-1 h-1 rounded-full bg-[#D4A574]"
                style={{
                  left: `${20 + i * 20}%`,
                  top: "-10px",
                }}
                animate={{
                  y: [0, -20, 0],
                  opacity: [0, 0.8, 0],
                  scale: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.3,
                  ease: "easeInOut",
                }}
              />
            ))}
          </>
        )}
      </motion.div>
    </motion.div>
  );
};

// Premium 3D Film Roll Carousel Component
interface FilmRollCarouselProps {
  sketches: Sketch[];
  onSelectSketch: (sketch: Sketch, units: number) => void;
  focusedIndex: number;
  setFocusedIndex: (index: number) => void;
}

const FilmRollCarousel: React.FC<FilmRollCarouselProps> = ({ 
  sketches, 
  onSelectSketch, 
  focusedIndex,
  setFocusedIndex 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [mouseX, setMouseX] = useState(0);
  const lastMouseX = useRef(0);
  const velocity = useRef(0);
  const animationRef = useRef<number>();
  
  const itemCount = sketches.length;
  const anglePerItem = 360 / itemCount;
  
  // Smooth rotation based on focused index
  const targetRotation = -focusedIndex * anglePerItem;
  const [currentRotation, setCurrentRotation] = useState(targetRotation);

  // Animate rotation smoothly - CLOCKWISE ONLY (no reverse)
  useEffect(() => {
    const animate = () => {
      setCurrentRotation(prev => {
        const diff = targetRotation - prev;
        // Always rotate clockwise - if diff is positive (would go counter-clockwise), go the long way around
        let adjustedDiff = diff;
        if (diff > 0) {
          // Convert to clockwise direction (negative rotation)
          adjustedDiff = diff - 360;
        }
        // Slower rotation speed (0.05) for smoother, more elegant movement
        const newRotation = prev + adjustedDiff * 0.05;
        return Math.abs(adjustedDiff) < 0.1 ? targetRotation : newRotation;
      });
      animationRef.current = requestAnimationFrame(animate);
    };
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [targetRotation]);

  // Auto-rotate when not hovered - slower interval for user-friendly experience
  useEffect(() => {
    if (!isHovered) {
      const interval = setInterval(() => {
        setFocusedIndex((focusedIndex + 1) % itemCount);
      }, 6000); // 6 seconds for gentler auto-rotation
      return () => clearInterval(interval);
    }
  }, [isHovered, focusedIndex, itemCount, setFocusedIndex]);

  // Throttle ref to prevent too rapid rotation
  const lastRotationTime = useRef(0);
  const rotationCooldown = 400; // ms between rotations for smoother UX

  // Handle mouse movement for rotation - CLOCKWISE ONLY
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    
    // Calculate mouse movement delta (positive = moving right)
    const deltaX = x - lastMouseX.current;
    lastMouseX.current = x;
    setMouseX(x);

    // Only rotate clockwise when mouse moves (any horizontal movement triggers clockwise rotation)
    if (isHovered && Math.abs(deltaX) > 5) {
      const now = Date.now();
      // Throttle rotation for smooth, controlled movement
      if (now - lastRotationTime.current > rotationCooldown) {
        // Always move clockwise (next item) regardless of mouse direction
        const newIndex = (focusedIndex + 1) % itemCount;
        setFocusedIndex(newIndex);
        lastRotationTime.current = now;
      }
    }
  }, [isHovered, focusedIndex, itemCount, setFocusedIndex]);

  // Click to focus a specific sketch AND open detail panel
  const handleSketchClick = (index: number) => {
    setFocusedIndex(index);
    // Open detail panel for the clicked sketch
    onSelectSketch(sketches[index], 300);
  };

  const radius = 320;

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[550px] md:h-[650px] flex items-center justify-center cursor-grab active:cursor-grabbing"
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ perspective: "1400px" }}
    >
      {/* Film Roll Frame */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Film sprocket holes - top */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 flex gap-5">
          {[...Array(16)].map((_, i) => (
            <motion.div
              key={`top-${i}`}
              className="w-2.5 h-4 rounded-sm"
              style={{
                background: "linear-gradient(180deg, #0A0705 0%, #1A0F0A 100%)",
                boxShadow: "inset 0 1px 2px rgba(0,0,0,0.8)",
              }}
              animate={{ opacity: [0.6, 0.8, 0.6] }}
              transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 }}
            />
          ))}
        </div>

        {/* Film sprocket holes - bottom */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-5">
          {[...Array(16)].map((_, i) => (
            <motion.div
              key={`bottom-${i}`}
              className="w-2.5 h-4 rounded-sm"
              style={{
                background: "linear-gradient(180deg, #0A0705 0%, #1A0F0A 100%)",
                boxShadow: "inset 0 1px 2px rgba(0,0,0,0.8)",
              }}
              animate={{ opacity: [0.6, 0.8, 0.6] }}
              transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 + 0.5 }}
            />
          ))}
        </div>

        {/* Film edge strips */}
        <div 
          className="absolute top-0 left-0 right-0 h-8"
          style={{
            background: "linear-gradient(180deg, rgba(26,15,10,0.9) 0%, transparent 100%)",
          }}
        />
        <div 
          className="absolute bottom-0 left-0 right-0 h-8"
          style={{
            background: "linear-gradient(0deg, rgba(26,15,10,0.9) 0%, transparent 100%)",
          }}
        />
      </div>

      {/* 3D Carousel Container */}
      <div
        className="relative"
        style={{
          transformStyle: "preserve-3d",
          transform: `rotateY(${currentRotation}deg)`,
        }}
      >
        {sketches.map((sketch, index) => {
          const angle = anglePerItem * index;
          const radian = (angle * Math.PI) / 180;
          const x = Math.sin(radian) * radius;
          const z = Math.cos(radian) * radius;
          
          // Calculate relative position for styling
          const relativeAngle = ((currentRotation + angle) % 360 + 360) % 360;
          const isFocused = index === focusedIndex;
          const distanceFromFront = Math.abs(relativeAngle > 180 ? 360 - relativeAngle : relativeAngle);
          const opacity = Math.max(0.3, 1 - distanceFromFront / 180);
          const scale = isFocused ? 1.15 : Math.max(0.7, 1 - distanceFromFront / 300);

          return (
            <Premium3DCard
              key={sketch.id}
              sketch={sketch}
              index={index}
              angle={angle}
              x={x}
              z={z}
              isFocused={isFocused}
              opacity={opacity}
              scale={scale}
              onClickCard={handleSketchClick}
            />
          );
        })}
      </div>

      {/* Center Focus Glow */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full pointer-events-none"
        style={{
          background: "radial-gradient(circle, rgba(212,165,116,0.1) 0%, transparent 60%)",
        }}
      />

      {/* Navigation Arrow - Clockwise Only */}
      <motion.button
        className="absolute right-4 top-1/2 -translate-y-1/2 w-14 h-14 rounded-full flex items-center justify-center z-10"
        style={{
          background: "linear-gradient(135deg, rgba(212,165,116,0.4) 0%, rgba(44,24,16,0.6) 100%)",
          border: "2px solid rgba(212,165,116,0.4)",
        }}
        whileHover={{ scale: 1.1, backgroundColor: "rgba(212,165,116,0.5)" }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setFocusedIndex((focusedIndex + 1) % itemCount)}
      >
        <ArrowRight className="w-6 h-6 text-white" />
      </motion.button>

      {/* Dot indicators */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex gap-2">
        {sketches.map((_, index) => (
          <motion.button
            key={index}
            className="w-2 h-2 rounded-full"
            style={{
              background: index === focusedIndex ? "#D4A574" : "rgba(212,165,116,0.3)",
            }}
            whileHover={{ scale: 1.3 }}
            onClick={() => setFocusedIndex(index)}
          />
        ))}
      </div>
    </div>
  );
};

// Product Detail Panel with Unit Selection
interface DetailPanelProps {
  sketch: Sketch | null;
  categoryTitle: string;
  selectedUnits: number;
  onClose: () => void;
}

const DetailPanel: React.FC<DetailPanelProps> = ({ sketch, categoryTitle, selectedUnits, onClose }) => {
  const { t } = useTranslation();
  const [units, setUnits] = useState(selectedUnits);
  
  if (!sketch) return null;

  return (
    <motion.div
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.85, opacity: 1, y: 50, rotateX: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0, rotateX: 0 }}
        exit={{ scale: 0.85, opacity: 0, y: 50, rotateX: -10 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="relative max-w-4xl w-full max-h-[90vh] overflow-y-auto rounded-3xl"
        style={{ 
          background: "linear-gradient(145deg, #3D2B1F 0%, #2C1810 50%, #1A0F0A 100%)",
          boxShadow: "0 50px 100px rgba(0,0,0,0.5), 0 0 60px rgba(212,165,116,0.1)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <motion.button
          onClick={onClose}
          className="absolute top-6 right-6 z-10 p-3 rounded-full"
          style={{
            background: "linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
            border: "1px solid rgba(255,255,255,0.1)",
          }}
          whileHover={{ scale: 1.1, backgroundColor: "rgba(255,255,255,0.15)" }}
          whileTap={{ scale: 0.95 }}
        >
          <X className="w-5 h-5 text-white" />
        </motion.button>

        <div className="grid md:grid-cols-2 gap-8 p-8 md:p-10">
          {/* Product Image with 3D Effect */}
          <motion.div
            initial={{ x: -50, opacity: 1 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1, type: "spring", damping: 25 }}
            className="relative aspect-square rounded-2xl overflow-hidden flex items-center justify-center"
            style={{ 
              background: "linear-gradient(145deg, #FFF8F0 0%, #F5E6D3 50%, #E8DDD0 100%)",
              boxShadow: "inset 0 2px 4px rgba(255,255,255,0.3), 0 20px 40px rgba(0,0,0,0.3)",
            }}
          >
            <motion.img
              src={sketch.image.src || sketch.image}
              alt={sketch.name}
              className="max-w-[75%] max-h-[75%] object-contain"
              animate={{ 
                y: [0, -12, 0],
                rotateY: [0, 2, 0, -2, 0],
              }}
              transition={{ 
                y: { duration: 3, repeat: Infinity, ease: "easeInOut" },
                rotateY: { duration: 6, repeat: Infinity, ease: "easeInOut" },
              }}
              style={{ 
                filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.35))",
              }}
            />
            
            {/* Ambient glow */}
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                background: "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.3) 0%, transparent 50%)",
              }}
            />
          </motion.div>

          {/* Product Details */}
          <motion.div
            initial={{ x: 50, opacity: 1 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2, type: "spring", damping: 25 }}
            className="flex flex-col justify-center"
          >
            <motion.span 
              className="text-[#D4A574] text-sm font-medium tracking-[0.2em] uppercase mb-3"
              initial={{ opacity: 1, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              {categoryTitle}
            </motion.span>
            
            <motion.h2 
              className="text-white font-serif text-3xl md:text-4xl mb-4 leading-tight"
              initial={{ opacity: 1, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              {sketch.name}
            </motion.h2>
            
            <motion.p 
              className="text-white/70 leading-relaxed mb-8 text-base"
              initial={{ opacity: 1, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              {sketch.description}
            </motion.p>

            {/* Unit Selection */}
            <motion.div 
              className="mb-8"
              initial={{ opacity: 1, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 }}
            >
              <h4 className="text-white font-medium mb-4 text-sm tracking-wide">
                {t('productsPage.selectQuantity')}
              </h4>
              <div className="flex gap-4">
                <motion.button 
                  className={`flex-1 px-6 py-4 rounded-xl font-medium text-sm transition-all ${
                    units === 300 
                      ? "bg-[#D4A574] text-[#2C1810] shadow-lg" 
                      : "bg-[#D4A574]/15 border border-[#D4A574]/30 text-[#D4A574] hover:bg-[#D4A574]/25"
                  }`}
                  onClick={() => setUnits(300)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="block text-lg font-serif font-medium">300</span>
                  <span className="text-xs opacity-80">{t('productsPage.units')}</span>
                </motion.button>
                <motion.button 
                  className={`flex-1 px-6 py-4 rounded-xl font-medium text-sm transition-all ${
                    units === 500 
                      ? "bg-[#D4A574] text-[#2C1810] shadow-lg" 
                      : "bg-[#D4A574]/15 border border-[#D4A574]/30 text-[#D4A574] hover:bg-[#D4A574]/25"
                  }`}
                  onClick={() => setUnits(500)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="block text-lg font-serif font-medium">500</span>
                  <span className="text-xs opacity-80">{t('productsPage.units')}</span>
                </motion.button>
              </div>
            </motion.div>

            {/* CTA Button - Links to Book a Call with unit info */}
            <motion.div
              initial={{ opacity: 1, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Link 
                href={`/bookacall?product=${encodeURIComponent(sketch.name)}&units=${units}`}
              >
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button 
                    size="lg" 
                    className="w-full py-6 text-base bg-[#D4A574] hover:bg-[#C49464] text-[#2C1810] font-serif font-medium shadow-xl"
                    style={{
                      boxShadow: "0 10px 30px rgba(212,165,116,0.3)",
                    }}
                  >
                    {t('productsPage.requestQuoteUnits').replace('{units}', units.toString())}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </motion.div>
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Category Section with Premium Film Roll
interface CategorySectionProps {
  category: Category;
  index: number;
  translatedTitle: string;
}

const CategorySection: React.FC<CategorySectionProps> = ({ category, index, translatedTitle }) => {
  const { t } = useTranslation();
  const [selectedSketch, setSelectedSketch] = useState<Sketch | null>(null);
  const [selectedUnits, setSelectedUnits] = useState(300);
  const [focusedIndex, setFocusedIndex] = useState(0);

  const handleSelectSketch = (sketch: Sketch, units: number = 300) => {
    setSelectedSketch(sketch);
    setSelectedUnits(units);
  };

  const handleSketchClick = () => {
    // When focused sketch is clicked, open detail panel
    setSelectedSketch(category.sketches[focusedIndex]);
  };

  return (
    <>
      <section className="py-24 md:py-28 relative overflow-hidden"
        style={{
          background: index % 2 === 0
            ? "linear-gradient(180deg, #0A0705 0%, #1A0F0A 30%, #2C1810 50%, #1A0F0A 70%, #0A0705 100%)"
            : "linear-gradient(180deg, #1A0F0A 0%, #2C1810 30%, #3D2B1F 50%, #2C1810 70%, #1A0F0A 100%)",
        }}
      >
        {/* Background Pattern */}
        <div 
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `radial-gradient(circle at 20% 50%, rgba(212,165,116,0.3) 0%, transparent 50%),
                             radial-gradient(circle at 80% 50%, rgba(212,165,116,0.2) 0%, transparent 50%)`,
          }}
        />

        <div className="container mx-auto px-4">
          <div className="grid lg:grid-cols-[300px_1fr] gap-12 items-center">
            {/* Left - Category Info */}
            <motion.div
              initial={{ opacity: 1, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="lg:sticky lg:top-32"
            >
              <motion.span 
                className="text-[#D4A574]/50 text-xs font-medium tracking-[0.3em] uppercase mb-4 block"
                initial={{ opacity: 1 }}
                whileInView={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                Category {index + 1}
              </motion.span>
              <h2 className="font-serif text-4xl md:text-5xl lg:text-6xl text-white mb-6 leading-tight">
                {translatedTitle}
              </h2>
              <motion.div 
                className="w-20 h-1 bg-gradient-to-r from-[#D4A574] to-[#8B6914] mb-6"
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                style={{ originX: 0 }}
              />
              <p className="text-white/50 text-sm leading-relaxed mb-6">
                {t('productsPage.exploreCollection')} {translatedTitle.toLowerCase()} {t('productsPage.dragInstruction')}
              </p>
              <div className="flex items-center gap-3 text-[#D4A574]/70 text-sm">
                <span className="w-8 h-8 rounded-full bg-[#D4A574]/10 flex items-center justify-center text-xs font-serif font-medium">
                  {category.sketches.length}
                </span>
                <span>{t('productsPage.originalDesigns')}</span>
              </div>

              {/* Quick View Button */}
              <motion.button
                className="mt-8 px-6 py-3 rounded-xl text-sm font-medium"
                style={{
                  background: "linear-gradient(135deg, rgba(212,165,116,0.2) 0%, rgba(212,165,116,0.1) 100%)",
                  border: "1px solid rgba(212,165,116,0.3)",
                  color: "#D4A574",
                }}
                whileHover={{ scale: 1.02, backgroundColor: "rgba(212,165,116,0.25)" }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSketchClick}
              >
                {t('productsPage.viewCurrentDesign')}
                <ArrowRight className="w-4 h-4 ml-2 inline" />
              </motion.button>
            </motion.div>

            {/* Center - Premium Film Roll Carousel */}
            <div className="relative">
              <FilmRollCarousel
                sketches={category.sketches}
                onSelectSketch={handleSelectSketch}
                focusedIndex={focusedIndex}
                setFocusedIndex={setFocusedIndex}
              />
              
              {/* Instructions */}
              <motion.div
                className="text-center mt-6"
                initial={{ opacity: 1 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <p className="text-white/30 text-xs tracking-wide">
                  {t('productsPage.hoverInstruction')}
                </p>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      <AnimatePresence>
        {selectedSketch && (
          <DetailPanel 
            sketch={selectedSketch} 
            categoryTitle={category.title} 
            selectedUnits={selectedUnits}
            onClose={() => setSelectedSketch(null)} 
          />
        )}
      </AnimatePresence>
    </>
  );
};

const Products = () => {
  const { t } = useTranslation();
  
  // Function to get translated category title
  const getCategoryTitle = (categoryId: string) => {
    switch(categoryId) {
      case 'belts':
        return t('productsPage.beltsCategory');
      case 'bags':
        return t('productsPage.bagsCategory');
      case 'wallets':
        return t('productsPage.walletsCategory');
      default:
        return categoryId;
    }
  };
  
  return (
    <>
      {/* Hero Section */}
      <section className="relative pt-32 pb-24 bg-charcoal overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${leatherCraftsmanBg.src})` }} />
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Side - Text Content */}
            <motion.div
              initial={{ opacity: 1, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="text-left"
            >
              <motion.span 
                initial={{ opacity: 1, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="text-saddle-tan font-medium tracking-widest uppercase text-sm mb-6 block"
              >
                {t('productsPage.badge')}
              </motion.span>
              <motion.h1
                className="text-4xl md:text-5xl lg:text-6xl text-warm-beige mb-6 leading-tight"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3 }}
              >
                {t('productsPage.title')} <span className="text-saddle-tan">{t('productsPage.titleHighlight')}</span>
              </motion.h1>
              <motion.p
                className="text-xl text-warm-beige/80 leading-relaxed mb-10"
                initial={{ opacity: 1, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                {t('productsPage.heroSubtitle')}
              </motion.p>
            </motion.div>

            {/* Right Side - Enhanced Product Showcase */}
            <motion.div
              initial={{ opacity: 1, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
              className="relative"
            >
              {/* Premium Showcase Container */}
              <div className="relative bg-gradient-to-br from-[#2C1810]/40 to-[#1A0F0A]/40 backdrop-blur-md rounded-3xl p-6 border border-saddle-tan/20 shadow-2xl">
                
                {/* Top Label */}
                <motion.div
                  initial={{ opacity: 1, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 }}
                  className="text-center mb-6"
                >
                  <span className="inline-block px-4 py-1 bg-saddle-tan/20 rounded-full border border-saddle-tan/40 text-saddle-tan text-xs font-serif font-normal tracking-wider">
                    {t('productsPage.catalogBadge')}
                  </span>
                </motion.div>

                {/* Main Product Grid - Enhanced */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {/* Belts Column */}
                  <div className="space-y-3">
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 }}
                      whileHover={{ y: -5, scale: 1.02 }}
                      className="relative group cursor-pointer"
                    >
                      <div className="relative bg-gradient-to-br from-warm-beige/15 to-warm-beige/5 backdrop-blur-sm border-2 border-saddle-tan/40 rounded-2xl p-4 hover:border-saddle-tan hover:shadow-xl hover:shadow-saddle-tan/20 transition-all duration-300">
                        {/* Product Image with Shadow */}
                        <div className="relative mb-3">
                          <div className="absolute inset-0 bg-saddle-tan/10 blur-xl" />
                          <img 
                            src={ClassicSquareBuckleBelt.src} 
                            alt="Belt"
                            className="relative w-full h-32 object-contain drop-shadow-2xl"
                          />
                        </div>
                        
                        {/* Product Info */}
                        <div className="text-center">
                          <p className="text-saddle-tan font-serif font-medium text-sm mb-1">{t('productsPage.beltsCategory')}</p>
                          <p className="text-warm-beige/70 text-xs">12 {t('productsPage.uniqueDesigns')}</p>
                        </div>

                        {/* Hover Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-saddle-tan/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl" />
                        
                        {/* Corner Accent */}
                        <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                        <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                      </div>
                    </motion.div>

                    {/* Secondary Belt Card */}
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.9 }}
                      whileHover={{ scale: 1.05 }}
                      className="relative bg-warm-beige/5 backdrop-blur-sm border border-warm-beige/20 rounded-xl p-3 hover:border-saddle-tan/50 transition-all duration-300 cursor-pointer"
                    >
                      <img 
                        src={StuddedLeatherBelt.src} 
                        alt="Belt Variant"
                        className="w-full h-20 object-contain opacity-70 hover:opacity-100 transition-opacity"
                      />
                    </motion.div>
                  </div>

                  {/* Bags Column */}
                  <div className="space-y-3">
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 }}
                      whileHover={{ y: -5, scale: 1.02 }}
                      className="relative group cursor-pointer"
                    >
                      <div className="relative bg-gradient-to-br from-warm-beige/15 to-warm-beige/5 backdrop-blur-sm border-2 border-saddle-tan/40 rounded-2xl p-4 hover:border-saddle-tan hover:shadow-xl hover:shadow-saddle-tan/20 transition-all duration-300">
                        {/* Product Image with Shadow */}
                        <div className="relative mb-3">
                          <div className="absolute inset-0 bg-saddle-tan/10 blur-xl" />
                          <img 
                            src={Satchel.src} 
                            alt="Bag"
                            className="relative w-full h-32 object-contain drop-shadow-2xl"
                          />
                        </div>
                        
                        {/* Product Info */}
                        <div className="text-center">
                          <p className="text-saddle-tan font-serif font-medium text-sm mb-1">{t('productsPage.bagsCategory')}</p>
                          <p className="text-warm-beige/70 text-xs">10 {t('productsPage.uniqueDesigns')}</p>
                        </div>

                        {/* Hover Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-saddle-tan/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl" />
                        
                        {/* Corner Accent */}
                        <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                        <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                      </div>
                    </motion.div>

                    {/* Secondary Bag Card */}
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.0 }}
                      whileHover={{ scale: 1.05 }}
                      className="relative bg-warm-beige/5 backdrop-blur-sm border border-warm-beige/20 rounded-xl p-3 hover:border-saddle-tan/50 transition-all duration-300 cursor-pointer"
                    >
                      <img 
                        src={MessengerBackpack.src} 
                        alt="Bag Variant"
                        className="w-full h-20 object-contain opacity-70 hover:opacity-100 transition-opacity"
                      />
                    </motion.div>
                  </div>

                  {/* Wallets Column */}
                  <div className="space-y-3">
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.8 }}
                      whileHover={{ y: -5, scale: 1.02 }}
                      className="relative group cursor-pointer"
                    >
                      <div className="relative bg-gradient-to-br from-warm-beige/15 to-warm-beige/5 backdrop-blur-sm border-2 border-saddle-tan/40 rounded-2xl p-4 hover:border-saddle-tan hover:shadow-xl hover:shadow-saddle-tan/20 transition-all duration-300">
                        {/* Product Image with Shadow */}
                        <div className="relative mb-3">
                          <div className="absolute inset-0 bg-saddle-tan/10 blur-xl" />
                          <img 
                            src={ClassicBifoldWallet.src} 
                            alt="Wallet"
                            className="relative w-full h-32 object-contain drop-shadow-2xl"
                          />
                        </div>
                        
                        {/* Product Info */}
                        <div className="text-center">
                          <p className="text-saddle-tan font-serif font-medium text-sm mb-1">{t('productsPage.walletsCategory')}</p>
                          <p className="text-warm-beige/70 text-xs">12 {t('productsPage.uniqueDesigns')}</p>
                        </div>

                        {/* Hover Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-saddle-tan/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl" />
                        
                        {/* Corner Accent */}
                        <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                        <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-saddle-tan/50 group-hover:border-saddle-tan transition-colors" />
                      </div>
                    </motion.div>

                    {/* Secondary Wallet Card */}
                    <motion.div
                      initial={{ opacity: 1, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.1 }}
                      whileHover={{ scale: 1.05 }}
                      className="relative bg-warm-beige/5 backdrop-blur-sm border border-warm-beige/20 rounded-xl p-3 hover:border-saddle-tan/50 transition-all duration-300 cursor-pointer"
                    >
                      <img 
                        src={PassportHolder.src} 
                        alt="Wallet Variant"
                        className="w-full h-20 object-contain opacity-70 hover:opacity-100 transition-opacity"
                      />
                    </motion.div>
                  </div>
                </div>

                {/* Bottom Stats Bar */}
                <motion.div
                  initial={{ opacity: 1, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2 }}
                  className="flex items-center justify-between pt-4 border-t border-saddle-tan/20"
                >
                  <div className="flex items-center gap-2 text-warm-beige/60 text-xs">
                    <div className="w-2 h-2 rounded-full bg-saddle-tan animate-pulse" />
                    <span>34 {t('productsPage.productCount')}</span>
                  </div>
                  <div className="flex items-center gap-2 text-warm-beige/60 text-xs">
                    <span>{t('productsPage.premiumQuality')}</span>
                    <div className="w-2 h-2 rounded-full bg-saddle-tan animate-pulse" />
                  </div>
                </motion.div>

                {/* Decorative Corner Elements */}
                <div className="absolute -top-2 -left-2 w-8 h-8 border-t-2 border-l-2 border-saddle-tan/30 rounded-tl-2xl" />
                <div className="absolute -top-2 -right-2 w-8 h-8 border-t-2 border-r-2 border-saddle-tan/30 rounded-tr-2xl" />
                <div className="absolute -bottom-2 -left-2 w-8 h-8 border-b-2 border-l-2 border-saddle-tan/30 rounded-bl-2xl" />
                <div className="absolute -bottom-2 -right-2 w-8 h-8 border-b-2 border-r-2 border-saddle-tan/30 rounded-br-2xl" />
              </div>

              {/* Ambient Glow Effects - Static, No Rotation */}
              <div className="absolute -inset-4 -z-10">
                <div className="absolute top-0 left-1/4 w-32 h-32 bg-saddle-tan/20 rounded-full blur-3xl" />
                <div className="absolute bottom-0 right-1/4 w-40 h-40 bg-saddle-tan/15 rounded-full blur-3xl" />
              </div>

              {/* Floating Particles - Static Positions */}
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 1 }}
                  animate={{ 
                    opacity: [0.2, 0.5, 0.2],
                    y: [0, -10, 0]
                  }}
                  transition={{
                    duration: 3 + i,
                    repeat: Infinity,
                    delay: i * 0.5,
                  }}
                  className="absolute w-1 h-1 bg-saddle-tan rounded-full"
                  style={{
                    top: `${20 + (i * 15)}%`,
                    left: i % 2 === 0 ? '5%' : '95%',
                  }}
                />
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* Design Sketches Intro */}
      <section className="py-24 bg-gradient-to-b from-charcoal via-[#1A0F0A] to-[#0A0705]">
  <div className="text-center container mx-auto px-4">
    <motion.div
      initial={{ opacity: 1, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.8 }}
      className="max-w-4xl mx-auto"
    >
      <h2 className="font-serif text-4xl md:text-5xl lg:text-6xl text-warm-beige mt-4 mb-6">
        {t('productsPage.showcaseTitle')}
        <span className="text-saddle-tan"> {t('productsPage.showcaseTitleHighlight')} </span>
      </h2>

      <p className="text-warm-beige/60 leading-relaxed text-lg">
        {t('productsPage.showcaseSubtitle')}
        <span className="text-[#D4A574] ml-2 block md:inline">
          {t('productsPage.showcaseSubtitle2')}
        </span>
      </p>
    </motion.div>
  </div>
</section>


      {/* Category Sections */}
      {categoriesData.map((category, index) => (
        <CategorySection 
          key={category.id} 
          category={category} 
          index={index} 
          translatedTitle={getCategoryTitle(category.id)}
        />
      ))}

      {/* CTA Section */}
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
      <h2 className="font-serif text-4xl text-warm-beige mb-6">
        {t('productsPage.ctaTitle')}{" "}
        <span className="text-saddle-tan">{t('productsPage.ctaTitleHighlight')}</span>{t('productsPage.ctaTitleEnd')}
      </h2>

      <p className="text-warm-beige/80 mb-8">
        {t('productsPage.ctaSubtitle')}
      </p>

      <Link href="/bookacall">
        <div className="leather-stitch-box inline-block">
          <Button
            className="bg-saddle-tan hover:bg-saddle-tan/90 text-charcoal font-serif font-normal"
            size="lg"
          >
            {t('productsPage.ctaButton')}
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

export default Products;
