// FAQ Data — KRITIKAAL.COM
// Prepared by Adam (COO) | Applied all 5 CEO-approved changes
// Source: faq-PUBLICATION-READY.md
// All 29 entries ready for deployment — no placeholders.

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category?: string;
}

export const faqData: FAQItem[] = [
  {
    id: "faq-01",
    category: "managed-manufacturing",
    question:
      "What is managed leather manufacturing and how is it different from going direct to a leather manufacturer in India?",
    answer:
      "Managed leather manufacturing means KRITIKAAL — India's managed leather manufacturing partner — sits between your brand and our vetted factory network, handling every step on your behalf: factory selection, sample development, in-line quality control, compliance documentation, and export logistics. When you go direct to a leather manufacturer in India, you own every problem that arises — communication breakdowns, QC failures, missing compliance documents, and delivery delays. With KRITIKAAL you have a Single Point of Accountability — one English-speaking contact who manages everything on the ground in India.",
  },
  {
    id: "faq-02",
    category: "quality-control",
    question:
      "My last leather bag order from a manufacturer in India had major quality defects. How does KRITIKAAL prevent this?",
    answer:
      "Most quality failures happen because there is no inspection during production — only at delivery, when nothing can be fixed. KRITIKAAL conducts in-line QC at 30% of production, catching colour, stitching, construction, and hardware problems before the full batch is made — whether the order is for leather bags, footwear, wallets, or garments. We then conduct a final AQL 2.5 inspection before any carton is packed. The full inspection report with photos is shared with you before packing begins. You approve before the container is sealed. Any batch that fails AQL 2.5 is covered by our Double-Back Guarantee — defective units are fixed or replaced at our cost before shipment.",
  },
  {
    id: "faq-03",
    category: "moq-oem",
    question:
      "What is the minimum order quantity for leather goods from India — and do you offer OEM and private label manufacturing?",
    answer:
      "KRITIKAAL's standard MOQ is 300 units per style. For first-time buyers, trial orders are accepted from 150 units at a small premium. We offer full OEM leather manufacturing from India — where we manufacture to your exact specifications — and private label leather manufacturing from India, including your brand's own labels, embossed or debossed logo, custom hardware, custom lining, and branded packaging. We can offer these lower MOQs because we aggregate orders across multiple buyers for the same factory.",
  },
  {
    id: "faq-04",
    category: "communication",
    question:
      "The leather manufacturer in India I worked with stopped responding mid-production. How does KRITIKAAL handle communication for UK, German, and European brands?",
    answer:
      "This is the most common complaint from brands — including UK, German, and European buyers — who have sourced directly from a leather manufacturer in India. A factory floor manager is running multiple production lines and responding to international messages is not their priority. At KRITIKAAL, every buyer has a dedicated English-speaking account manager. You receive WhatsApp updates at every milestone: leather approved, cutting started, in-line QC passed, final inspection report, packing complete, container booked, tracking number shared. Available during GMT, CET, and AEST business hours.",
  },
  {
    id: "faq-05",
    category: "compliance-eu",
    question:
      "What REACH compliance documentation do I need to import leather goods into the EU — and does KRITIKAAL provide this for German and European brands?",
    answer:
      "For EU-bound leather goods — including orders for brands in Germany, France, Italy, Netherlands, and Scandinavia — you need five documents: a REACH declaration (Regulation EC 1907/2006), an azo dye test report from an accredited lab, a Chromium VI test report (EN ISO 17075-2, max 3mg/kg), a nickel release test for all metal hardware (EN 1811), and phthalates compliance for any plastic components. KRITIKAAL provides all five as standard on every EU order, tested by SGS or Bureau Veritas. Germany is India's largest leather export market in Europe — KRITIKAAL is an experienced managed leather manufacturing partner for German brands specifically.",
  },
  {
    id: "faq-06",
    category: "quality-control",
    question:
      "What is AQL 2.5 and do I need it for leather shoe and footwear orders from India?",
    answer:
      "AQL stands for Acceptance Quality Limit. AQL 2.5 is the international inspection standard used by H&M, Marks & Spencer, ASOS, and Next to inspect leather goods — including leather shoes, boots, bags, and accessories — manufactured in India before shipment. From a batch of 500 units, a certified inspector randomly checks a defined sample. If defects exceed 2.5%, the batch is held. Critical defects have zero tolerance. KRITIKAAL is a leather shoe manufacturer in India (Agra cluster) and applies AQL 2.5 as a standard on every footwear and leather goods order — not an optional extra.",
  },
  {
    id: "faq-07",
    category: "pricing-logistics",
    question:
      "I budgeted based on the FOB price from an Indian leather manufacturer. Why was my landed cost so much higher — and how does this work for Australian brands?",
    answer:
      "FOB is just the factory price. Your full landed cost adds sea freight, destination port handling, customs clearance, import duty, VAT on import, and delivery to warehouse. On a USD 18 FOB unit, landed cost in the UK or Germany is typically USD 26–29. For Australian brands importing leather goods from India, sea freight from Nhava Sheva to Sydney is 18–22 days and GSP Form A enables preferential tariff rates. KRITIKAAL provides a full landed cost estimate for your specific destination — UK, EU, USA, or Australia — before you confirm the order.",
  },
  {
    id: "faq-08",
    category: "lead-times",
    question:
      "What is the lead time for leather jackets, belts, bags, and footwear manufactured in India?",
    answer:
      "Lead times from sample approval to shipment: leather bags and small leather goods 45–60 days, leather footwear 50–65 days, leather jacket manufacturer India lead time 50–60 days, leather belt manufacturer India lead time 35–50 days. Proto sample from tech pack: 10–14 working days. Sea freight to UK: 22–26 days. Sea freight to Germany: 20–24 days. Sea freight to USA: 22–25 days. Sea freight to Australia: 18–22 days. Air freight to any destination: 5–7 days.",
  },
  {
    id: "faq-09",
    category: "clusters",
    question:
      "Which Indian leather cluster is right for my product — Agra, Kanpur, or Kolkata — and what does each one make best?",
    answer:
      "The cluster depends on your product. Agra produces 65% of India's leather footwear — right for boots, oxfords, loafers, and heels. Kanpur is India's leather wallet manufacturer hub and small leather goods capital — right for wallets, cardholders, belts, and straps. Kolkata has a long history of bag and garment manufacturing for European buyers — right for tote bags, crossbody bags, leather jackets, and corporate bags. Kanpur also leads on leather accessories manufacturing in India — key fobs, lanyards, straps, travel organisers. KRITIKAAL matches your brief to the correct cluster, not just the nearest factory.",
  },
  {
    id: "faq-10",
    category: "compliance-usa",
    question:
      "What CA65 / Prop 65 compliance documentation do I need for leather goods sold in the USA — and how does KRITIKAAL help US brands?",
    answer:
      "For US brands importing leather goods from India, California Proposition 65 requires testing against OEHHA thresholds for lead, cadmium, chromium VI, and other listed chemicals. KRITIKAAL is an experienced leather manufacturer India USA brands partner — we test all US-bound orders through SGS against CA65 thresholds and provide the full compliance documentation as standard. We also provide CBP ISF 10+2 data for your customs broker, correct HTS codes, and GSP Certificate of Origin. CIF Los Angeles: 22–25 days from Nhava Sheva.",
  },
  {
    id: "faq-11",
    category: "quality-control",
    question:
      "My sample from India was perfect but the bulk order had different quality. How does this compare to sourcing from China?",
    answer:
      "Samples are sometimes made by a senior craftsman in a showroom. Bulk happens on the factory floor under production pressure without the same oversight. This is not unique to India — it happens with direct factory orders from China too. However, India vs China leather manufacturing has one key difference: India's cluster-based artisan skills (Agra footwear, Kanpur SLG, Kolkata bags) produce genuine leather quality that Chinese mass production cannot replicate. The solution in both countries is a managed manufacturing model with in-line QC at 30% of production — which is KRITIKAAL's standard on every order.",
  },
  {
    id: "faq-12",
    category: "payment",
    question:
      "What payment terms does KRITIKAAL offer for leather manufacturing orders from India?",
    answer:
      "Standard for first orders: 30–50% advance payment to confirm production, balance against the Bill of Lading copy when goods are shipped. KRITIKAAL supports TT (Telegraphic Transfer), LC (Letter of Credit), and escrow payment for first-time buyers. Deferred payment terms (30–60 days net) are available to established clients from the third order onwards. We do not require 100% upfront payment on any order.",
  },
  {
    id: "faq-13",
    category: "getting-started",
    question:
      "Can KRITIKAAL develop a leather product from scratch if I don't have a tech pack — and how do I source leather goods from India as a first-time buyer?",
    answer:
      "Yes. If you have a reference sample, sketch, or photo of a similar product, KRITIKAAL's team develops the full tech pack including construction details, Pantone references, material specifications, and hardware callouts. This is how most brands source leather goods from India for the first time — they bring a concept, we develop it into a manufacturable specification. Tech pack development is included in the sample cost. Proto sample is typically ready 10–14 working days after the brief is approved.",
  },
  {
    id: "faq-14",
    category: "logistics",
    question:
      "What shipping terms (Incoterms) does KRITIKAAL offer for leather goods manufactured in India?",
    answer:
      "KRITIKAAL offers FOB Nhava Sheva (Mumbai), CIF to any destination port, and DDP (Delivered Duty Paid) to the UK, EU, USA, Australia, and Israel. DDP means one price, all-inclusive — KRITIKAAL manages export clearance in India, freight, import customs clearance at destination, and delivery to your warehouse. No hidden charges.",
  },
  {
    id: "faq-15",
    category: "verification",
    question:
      "How do I find and verify a reliable leather manufacturer in India — and what makes KRITIKAAL the best option for global brands?",
    answer:
      "To find a reliable leather manufacturer in India, verify five things: ask for an AQL 2.5 inspection report from a recent order — any factory that conducts this will produce it immediately. Request REACH or CA65 compliance certificates from an accredited lab (SGS, Bureau Veritas, Intertek) — self-declarations are not compliance. Verify the production factory address, not the showroom. Ask about in-line QC at 30% of production. Check export history to your specific market. KRITIKAAL is India's managed leather manufacturing partner that passes all five criteria and manages every verification on your behalf — making us the best leather manufacturer India option for global brands who want quality without complexity.",
  },
  {
    id: "faq-16",
    category: "sustainability",
    question:
      "What sustainability certifications can KRITIKAAL arrange for leather goods from India?",
    answer:
      "KRITIKAAL works with factories holding or working toward LWG (Leather Working Group) certification — the gold standard used by H&M, Nike, Gucci, and ASOS. We also work with BSCI-audited factories for buyers in Germany and Scandinavia. Oeko-Tex Standard 100 product certification is available on request. SA8000 social accountability documentation is available for buyers whose retail partners require it.",
  },
  {
    id: "faq-17",
    category: "materials",
    question:
      "What leather types does KRITIKAAL work with — full-grain, top-grain, or genuine leather?",
    answer:
      "KRITIKAAL works exclusively with full-grain and top-grain leather sourced from certified Indian tanneries. Full-grain leather uses the entire surface of the hide with the natural grain intact — the most durable grade, used for premium bags, heritage footwear, and fine wallets. Top-grain leather is lightly sanded for a uniform finish — durable and the most common choice for fashion brands. We do not produce bonded leather or PU leather products. All hides are traceable from tannery to finished product.",
  },
  {
    id: "faq-18",
    category: "israel",
    question:
      "How does KRITIKAAL handle leather manufacturing orders for Israeli buyers specifically?",
    answer:
      "KRITIKAAL works directly with brands and importers in Tel Aviv, Jerusalem, and Haifa. We provide full English-language documentation to Israeli customs standards including Commercial Invoice, Packing List, Certificate of Origin, Bill of Lading, and all compliance certificates. Non-bovine leather — goat, sheep, buffalo — is available for buyers with specific sourcing requirements. Air freight from Nhava Sheva to Ben Gurion International Airport: 5–7 days. Sea freight to Ashdod Port: 18–22 days. DDP Tel Aviv available. TT, LC, and escrow payment options all accepted.",
  },
  {
    id: "faq-19",
    category: "documentation",
    question:
      "What is the full list of export documents KRITIKAAL provides with every leather goods order from India?",
    answer:
      "Standard documentation on every order: Commercial Invoice, Packing List, Bill of Lading (sea) or Airway Bill (air), Certificate of Origin (GSP Form A), REACH compliance declaration and lab test reports (EU and UK orders), CA65 compliance reports (USA orders), AQL 2.5 inspection report with photographs, and Packing declaration. On request: BSCI audit report, Oeko-Tex certificate, SGS or Bureau Veritas third-party inspection report, MSDS (Material Safety Data Sheet).",
  },
  {
    id: "faq-20",
    category: "getting-started",
    question:
      "How do I source leather goods from India and start working with KRITIKAAL?",
    answer:
      "Sourcing leather goods from India through KRITIKAAL starts with one form at kritikaal.com/request-sample — tell us your product type, quantity, target market, and timeline. We respond within 24 hours with a production feasibility assessment. A 20-minute qualification call follows within 48 hours where we confirm the right cluster for your product, compliance requirements for your market, and realistic lead time. No commitment required to start. Proto sample ready 10–14 working days from brief approval. KRITIKAAL is India's managed leather manufacturing partner for brands in the UK, USA, Europe, Australia, and Israel — from 300 units per style.",
  },
  {
    id: "faq-21",
    category: "about-kritikaal",
    question:
      "Is KRITIKAAL a leather manufacturer in India or a sourcing agent?",
    answer:
      "KRITIKAAL is neither a factory nor a traditional sourcing agent. We are India's managed leather manufacturing partner — a model that sits between your brand and our vetted factory network across Agra, Kanpur, and Kolkata. Unlike a sourcing agent who introduces you to a factory and steps away, KRITIKAAL manages the entire process — sample development, production oversight, in-line QC, compliance documentation, and export logistics — from your first message to delivery at your warehouse. That is Single Point of Accountability in practice — one contact, complete responsibility, no handoffs.",
  },
  {
    id: "faq-22",
    category: "moq-oem",
    question:
      "Does KRITIKAAL offer OEM and private label leather manufacturing from India?",
    answer:
      "Yes. KRITIKAAL offers full OEM (Original Equipment Manufacturer) and private label leather manufacturing from India. For private label, we manufacture your product with your brand's own labels, hardware engraving, embossed or debossed logo, custom lining, and branded packaging. For OEM, we manufacture to your exact specifications and tech pack. Both services are available from 300 units per style. Lead time from sample approval: 45–60 days for bags and SLG, 50–65 days for footwear.",
  },
  {
    id: "faq-23",
    category: "products",
    question:
      "What leather bag categories does KRITIKAAL manufacture in India?",
    answer:
      "KRITIKAAL is a leather bag manufacturer in India operating from the Kolkata cluster. We manufacture tote bags, crossbody bags, clutch bags, backpacks, laptop bags, briefcases, shoppers, belt bags, and bucket bags. Available in full-grain and top-grain leather with custom hardware, Pantone-matched dyeing, custom lining, and private label branding. REACH and CA65 compliant. MOQ 300 units per style. Lead time 45–60 days from sample approval. Shipping FOB, CIF, or DDP to UK, USA, Europe, Australia, and Israel.",
  },
  {
    id: "faq-24",
    category: "products",
    question:
      "Does KRITIKAAL manufacture leather footwear, wallets, belts, jackets, and accessories in India?",
    answer:
      "Yes — KRITIKAAL manufactures across all leather goods categories from India's specialist clusters. Leather footwear (Agra cluster): boots, oxfords, loafers, heels, sneaker uppers. MOQ 300 pairs. Leather wallets and SLG (Kanpur cluster): bifold wallets, cardholders, passport holders, coin purses, RFID-blocking options. MOQ 300 units. Leather belts (Kanpur cluster): full-grain and top-grain, all hardware finishes. MOQ 300 units. Leather jackets and garments (Kolkata cluster): biker jackets, blazers, bombers, trench coats, waistcoats. MOQ 300 units. Leather accessories: key fobs, straps, lanyards, travel organisers, notebook covers. MOQ 300 units.",
  },
  {
    id: "faq-25",
    category: "india-vs-china",
    question:
      "India vs China leather manufacturing — which is better for my brand?",
    answer:
      "India wins on genuine leather quality and compliance. China wins on speed and synthetic leather volume. India's Agra, Kanpur, and Kolkata clusters have centuries of artisanal leather craft — particularly strong for full-grain footwear, SLG, and bags. Price comparison for leather bags (FOB): India USD 22–38, China USD 18–30. India's premium reflects genuine leather and artisan skill. Lead time: India 45–60 days, China 35–50 days. Compliance: India's REACH, CA65, and LWG certification capacity is growing rapidly. In 2025, most global brands moving from China to India cite quality, compliance confidence, and supply chain diversification as the three primary reasons.",
  },
  {
    id: "faq-26",
    category: "getting-started",
    question:
      "How do I source leather goods from India as a global brand?",
    answer:
      "Sourcing leather goods from India involves five steps. First, identify the right cluster for your product — Agra for footwear, Kanpur for SLG and belts, Kolkata for bags and garments. Second, choose between going direct to a factory or working with a managed manufacturing partner like KRITIKAAL. Third, develop a proto sample from your tech pack or reference — allow 10–14 working days. Fourth, confirm compliance documentation for your market before bulk begins — REACH for EU/UK, CA65 for USA, GSP Form A for tariff preference. Fifth, structure your payment correctly — 30–50% advance, balance against Bill of Lading. KRITIKAAL manages all five steps on your behalf from 300 units.",
  },
  {
    id: "faq-27",
    category: "verification",
    question:
      "How do I find a reliable leather manufacturer in India?",
    answer:
      "The five verification steps for any Indian leather manufacturer: ask for an AQL 2.5 inspection report from a recent order — a factory that conducts this will produce it immediately. Request REACH or CA65 compliance certificates from an accredited lab (SGS, Bureau Veritas, or Intertek) — self-declarations are not compliance. Visit or verify the production factory address, not the showroom — samples are sometimes made in a showroom while bulk happens elsewhere. Ask about in-line QC at 30% of production — factories that only inspect at the end leave you with no options if there are defects. Check their export history to your market. KRITIKAAL passes all five criteria and manages the verification process on your behalf.",
  },
  {
    id: "faq-28",
    category: "about-kritikaal",
    question:
      "Which is the best leather manufacturer in India for UK, German, Australian, and European brands?",
    answer:
      "The best leather manufacturer in India for international brands is one that combines artisanal manufacturing quality with managed services — compliance documentation, in-line QC, English-language communication, and export logistics handled as standard. KRITIKAAL is India's managed leather manufacturing partner operating across Agra (footwear), Kanpur (SLG and belts), and Kolkata (bags and garments). We work directly with brands and importers in the UK, Germany, France, Italy, Netherlands, Australia, and Israel. REACH compliance standard for EU and UK orders. CA65 compliance standard for US orders. GSP Form A standard for all orders. MOQ from 300 units.",
  },
  {
    id: "faq-29",
    category: "compliance-eu",
    question:
      "What is EUDR and does KRITIKAAL provide the required compliance documentation for leather goods imported into the EU?",
    answer:
      "The EU Deforestation Regulation (EUDR) enforcement begins June 2026. From that date, leather goods imported into the EU require an EUDR Due Diligence Statement — traceability documentation confirming the hides did not originate from recently deforested land. Most overseas supply chains cannot produce this documentation. A typical Indian leather factory has no farm-level geolocation data for their hides. No chain-of-custody records from farm to tannery. No tannery compliance trail. This is a shipment risk — not a paperwork issue. KRITIKAAL assembles the complete EUDR Due Diligence Statement for every EU-bound order. This includes: farm-level geolocation data for each hide batch, tannery sourcing declarations, and chain-of-custody documentation from farm to finished product. We work exclusively with LWG Gold certified tanneries — their traceability infrastructure is built for exactly this requirement. Enforcement means shipments without a valid EUDR Due Diligence Statement will be held at EU ports from June 2026. KRITIKAAL clients are compliant as standard — no additional cost, no additional timeline adjustment. If your current leather supplier cannot show you an EUDR Due Diligence Statement today, your June 2026 shipments are at risk. We have the documentation.",
  },
];

// Subset for homepage (first 5 most impactful questions)
export const homepageFaqData: FAQItem[] = faqData.slice(0, 5);
