import type { Metadata } from "next";
import RequestSampleClient from "./RequestSampleClient";

export const metadata: Metadata = {
  title: "Request Leather Sample | KRITIKAAL",
  description:
    "Start your leather sample development with KRITIKAAL. Submit your product requirements and begin manufacturing with full quality control and export support.",
};

export default function RequestSamplePage() {
  return <RequestSampleClient />;
}
