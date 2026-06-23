import { Hero } from "@/components/home/Hero";
import { CatalogueForm } from "@/components/home/CatalogueForm";
import { FAQ } from "@/components/home/FAQ";
import { HomeBlog } from "@/components/home/HomeBlog";
import { CTA } from "@/components/home/CTA";

export const revalidate = 3600;

export default function Index() {
  return (
    <>
      <Hero />
      <CatalogueForm />
      <FAQ />
      <HomeBlog />
      <CTA />
    </>
  );
}

