"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TranslationProvider } from "@/contexts/TranslationContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { PageTransition } from "@/components/PageTransition";
import { Layout } from "@/components/layout/Layout";
import { ReactNode, useState } from "react";

export function ClientProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <TranslationProvider>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <PageTransition>
            <Layout>
              {children}
            </Layout>
          </PageTransition>
        </TooltipProvider>
      </QueryClientProvider>
      <LanguageSwitcher />
    </TranslationProvider>
  );
}
