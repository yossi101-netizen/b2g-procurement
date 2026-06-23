import { productData } from "@/data/products";
import ProductDetailClient from "./ProductDetailClient";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export const revalidate = 3600;

export async function generateStaticParams() {
  return Object.keys(productData).map((id) => ({
    id: id,
  }));
}

export default function ProductDetailPage({ params }: { params: { id: string } }) {
  const product = productData[params.id];

  if (!product) {
    return (
      <section className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="font-serif text-4xl text-foreground mb-4">Product Not Found</h1>
          <p className="text-muted-foreground mb-8">The product you are looking for does not exist.</p>
          <Link href="/products">
            <Button variant="outline">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Products
            </Button>
          </Link>
        </div>
      </section>
    );
  }

  return <ProductDetailClient product={product} />;
}
