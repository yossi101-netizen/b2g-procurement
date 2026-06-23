"use client";

import { ReactNode } from "react";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";
import { CertificationStrip } from "./CertificationStrip";

interface LayoutProps {
  children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-14 sm:pt-16 md:pt-20 lg:pt-[85px]">
        {children}
      </main>
      <CertificationStrip />
      <Footer />
    </div>
  );
};
