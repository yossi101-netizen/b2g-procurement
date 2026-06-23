import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[9999] bg-charcoal flex items-center justify-center">
      <div className="text-center flex flex-col items-center">
        <Loader2 className="w-12 h-12 text-saddle-tan animate-spin mb-6" />
        <p className="text-saddle-tan font-serif font-light text-xl tracking-widest uppercase">
          KRITIKAAL
        </p>
        <p className="text-warm-beige/60 text-sm mt-3 tracking-wider">
          Preparing your experience...
        </p>
      </div>
    </div>
  );
}

