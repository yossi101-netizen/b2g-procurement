import ProductsClient from "./ProductsClient";

export const revalidate = 3600;

export default function ProductsPage() {
  return <ProductsClient />;
}
