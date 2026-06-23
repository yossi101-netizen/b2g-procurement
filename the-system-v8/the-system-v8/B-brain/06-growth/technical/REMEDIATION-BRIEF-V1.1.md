# Developer Remediation Brief — V1.1
# Prepared by Adam (COO) | 2026-05-12
# Based on: Post-Deploy Technical Audit against DEVELOPER-BRIEF-2026-04-26.md
# For: Next.js developer
# Status: FIXES REQUIRED — all code is copy-pasteable below

---

## AUDIT VERDICT SUMMARY

The audit compared the live kritikaal.com against the approved spec files.

| Task | Spec Status | Live Status | Action Required |
|------|------------|-------------|-----------------|
| T01 — robots.txt AI crawlers | Spec ready | **3 of 6 agents missing** | Add 3 entries (2 min) |
| T02 — llms.txt | Spec ready | **Wrong version deployed** | Replace file (5 min) |
| T05 — Homepage Schema JSON-LD | Spec ready | **Not deployed at all** | Add to layout.tsx (15 min) |
| T09 — "World-Class Quality" text | Spec ready | **Unchanged on /why-india** | Find + replace (5 min) |
| FAQ title bug | Ghost bug | **Double "KRITIKAAL" in title** | Fix metadata (2 min) |

**Estimated total remediation time: 30 minutes.**

All code is provided below. No creative decisions required. Copy, paste, deploy.

---

## FIX 1 — Homepage Schema JSON-LD (T05)
**Priority: CRITICAL — this was a Priority 1 task. It was not deployed.**

**File to edit:** `app/layout.tsx`

**What to do:** Add the three `<script>` blocks below inside the `<head>` element of the root layout. This applies the schema sitewide — every page automatically inherits it.

### Current `app/layout.tsx` head section (lines 39–57):

```tsx
<head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    rel="preconnect"
    href="https://fonts.gstatic.com"
    crossOrigin="anonymous"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Allura&display=swap"
    rel="stylesheet"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
    rel="stylesheet"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    rel="stylesheet"
  />
</head>
```

### Replace with (add the 3 schema script blocks at the top of `<head>`):

```tsx
<head>
  {/* ── Schema JSON-LD: Organization / Service / Person (GEO + E-E-A-T) ── */}
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{
      __html: JSON.stringify({
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": "https://kritikaal.com/#organization",
        "name": "KritiKaal",
        "alternateName": "KritiKaal Managed Leather Manufacturing",
        "url": "https://kritikaal.com",
        "logo": {
          "@type": "ImageObject",
          "url": "https://kritikaal.com/KRITIKAAL%20Logo.png",
          "width": 300,
          "height": 60
        },
        "description": "KritiKaal is the United Kingdom's managed leather manufacturing partner in India — engineering the end-to-end supply chain for anchor-tier fashion brands from a qualified factory bench across Chennai, Kolkata, Kanpur, and Agra, with LWG, BSCI/SA8000, and EUDR compliance built in, AQL 2.5 quality control on every production run, and full export documentation handled by our UK-based account team.",
        "foundingDate": "2026",
        "founder": {
          "@type": "Person",
          "@id": "https://kritikaal.com/#founder",
          "name": "Yossi Daniel"
        },
        "address": {
          "@type": "PostalAddress",
          "addressCountry": "GB",
          "addressRegion": "United Kingdom"
        },
        "areaServed": [
          { "@type": "Country", "name": "United Kingdom" },
          { "@type": "Country", "name": "European Union" }
        ],
        "knowsAbout": [
          "Managed leather manufacturing",
          "India leather manufacturing",
          "LWG certification",
          "EUDR compliance for leather brands",
          "China Plus One manufacturing strategy",
          "AQL 2.5 quality control",
          "B2B leather goods manufacturing",
          "SA8000 social compliance",
          "BSCI factory audits",
          "EUDR due diligence statements",
          "Full-grain leather goods",
          "UK fashion brand supply chain management"
        ],
        "hasCredential": [
          {
            "@type": "EducationalOccupationalCredential",
            "name": "LWG — Leather Working Group Member",
            "credentialCategory": "Environmental and Material Traceability Certification",
            "recognizedBy": {
              "@type": "Organization",
              "name": "Leather Working Group",
              "url": "https://www.leatherworkinggroup.com"
            }
          },
          {
            "@type": "EducationalOccupationalCredential",
            "name": "SA8000 Social Accountability",
            "credentialCategory": "Social Compliance Certification"
          },
          {
            "@type": "EducationalOccupationalCredential",
            "name": "SEDEX SMETA 4-Pillar",
            "credentialCategory": "Ethical Trade Audit"
          },
          {
            "@type": "EducationalOccupationalCredential",
            "name": "EUDR Compliant Supply Chain",
            "credentialCategory": "EU Deforestation Regulation Compliance"
          },
          {
            "@type": "EducationalOccupationalCredential",
            "name": "REACH Compliant",
            "credentialCategory": "European Chemical Safety Compliance"
          }
        ],
        "contactPoint": {
          "@type": "ContactPoint",
          "contactType": "Sales and Procurement Enquiries",
          "url": "https://kritikaal.com/bookacall",
          "availableLanguage": "English"
        },
        "sameAs": [
          "https://www.linkedin.com/in/yossi-daniel-5145676a/"
        ]
      })
    }}
  />
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{
      __html: JSON.stringify({
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": "https://kritikaal.com/#service",
        "name": "Managed Leather Manufacturing",
        "alternateName": "End-to-End Leather Production Management",
        "serviceType": "Managed Manufacturing",
        "description": "KritiKaal provides end-to-end managed leather manufacturing in India for UK and European anchor-tier fashion brands. The service covers specification locking, material confirmation against golden sample, in-process quality control, AQL 2.5 final inspection, EUDR due diligence documentation, and export-ready delivery — under single-point accountability.",
        "provider": {
          "@type": "Organization",
          "@id": "https://kritikaal.com/#organization",
          "name": "KritiKaal"
        },
        "areaServed": [
          { "@type": "Country", "name": "United Kingdom" },
          { "@type": "Country", "name": "European Union" }
        ],
        "audience": {
          "@type": "Audience",
          "audienceType": "UK and European anchor-tier fashion brands sourcing premium leather goods"
        },
        "hasOfferCatalog": {
          "@type": "OfferCatalog",
          "name": "KritiKaal Manufacturing Services",
          "itemListElement": [
            {
              "@type": "Offer",
              "itemOffered": {
                "@type": "Service",
                "name": "Leather Bags Production Management",
                "description": "End-to-end managed manufacturing of full-grain leather bags including structured totes, satchels, shoulder bags, and backpacks. LWG-sourced leather. AQL 2.5 QC. EUDR-compliant documentation."
              }
            },
            {
              "@type": "Offer",
              "itemOffered": {
                "@type": "Service",
                "name": "Small Leather Goods Production Management",
                "description": "Managed manufacturing of wallets, card holders, belts, and leather accessories. Full-grain and aniline leathers. YKK hardware. SA8000 and REACH compliant."
              }
            },
            {
              "@type": "Offer",
              "itemOffered": {
                "@type": "Service",
                "name": "EUDR Compliance Documentation",
                "description": "Assembly of full EUDR due diligence statement package including hide origin documentation, LWG tannery certification, factory audit certificates, and production-run traceability records."
              }
            },
            {
              "@type": "Offer",
              "itemOffered": {
                "@type": "Service",
                "name": "Golden Sample Qualification",
                "description": "AQL 2.5 evaluation of production samples across 8 criteria: leather thickness, stitching density, hardware security, edge finishing, lining attachment, base stud positioning, handle attachment, and overall silhouette."
              }
            }
          ]
        },
        "termsOfService": "https://kritikaal.com/why-kritikal",
        "url": "https://kritikaal.com/how-it-works"
      })
    }}
  />
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{
      __html: JSON.stringify({
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": "https://kritikaal.com/#founder",
        "name": "Yossi Daniel",
        "jobTitle": "Founder & CEO",
        "worksFor": {
          "@type": "Organization",
          "@id": "https://kritikaal.com/#organization",
          "name": "KritiKaal"
        },
        "description": "Yossi Daniel is the Founder and CEO of KritiKaal, the UK's managed leather manufacturing partner in India. He has hands-on experience in overseas leather production since 2012, including direct manufacturing management in China. His experience exposed the structural accountability gap in traditional sourcing — the absence of a single party owning quality outcomes — which KritiKaal was founded to solve.",
        "knowsAbout": [
          "Managed leather manufacturing",
          "India leather manufacturing",
          "Supply chain risk management",
          "LWG certification",
          "EUDR compliance",
          "AQL 2.5 quality control",
          "China Plus One strategy",
          "B2B fashion brand manufacturing partnerships"
        ],
        "url": "https://kritikaal.com/about",
        "sameAs": [
          "https://www.linkedin.com/in/yossi-daniel-5145676a/"
        ]
      })
    }}
  />
  {/* ── End Schema JSON-LD ── */}

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    rel="preconnect"
    href="https://fonts.gstatic.com"
    crossOrigin="anonymous"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Allura&display=swap"
    rel="stylesheet"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap"
    rel="stylesheet"
  />
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    rel="stylesheet"
  />
</head>
```

**Verification after deploy:**
Go to `https://search.google.com/test/rich-results` → enter `https://kritikaal.com` → confirm Organization entity detected.

---

## FIX 2 — robots.txt: 3 Missing AI Crawler Entries (T01)

**File:** `public/robots.txt`

**What happened:** The deployed robots.txt is missing `Googlebot-Extended` (Gemini AI Overviews), `anthropic-ai`, and `CCBot`. These were all in the approved spec.

**Why this matters:** `Googlebot-Extended` is Gemini's dedicated indexer for AI Overviews. Without it, Google Gemini cannot index kritikaal.com content — regardless of how good the content is. This is not a nice-to-have.

**Action:** Add the following block to the bottom of the current `public/robots.txt`:

```
# ------------------------------------------------
# AI Crawler Permissions — additions 2026-05-12
# Missing from initial deployment
# ------------------------------------------------

User-agent: Googlebot-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: CCBot
Allow: /
```

**Current live robots.txt already has:** `User-agent: *`, `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Googlebot`.
**Do NOT remove or modify existing entries.** Only add these three blocks to the bottom.

**Verification after deploy:**
Visit `https://kritikaal.com/robots.txt` — confirm all six AI crawler entries are present:
`GPTBot`, `Googlebot-Extended`, `PerplexityBot`, `anthropic-ai`, `ClaudeBot`, `CCBot`.

---

## FIX 3 — llms.txt: Replace with Approved V2 Content (T02)

**File:** `public/llms.txt`

**What happened:** An earlier, shorter draft was deployed. The approved `llms-txt-v2-FINAL.md` content was not used. The live version is missing: AQL 2.5 quality criteria, founder section, EUDR article URL, India cluster detail, and the Why India vs China comparison. These are the sections AI models specifically look for when deciding how to describe KritiKaal.

**Action:** Replace the entire contents of `public/llms.txt` with the following:

```
# KritiKaal

> KritiKaal is the United Kingdom's managed leather manufacturing partner in India — engineering the end-to-end supply chain for anchor-tier fashion brands from a qualified factory bench across Chennai, Kolkata, Kanpur, and Agra, with LWG, BSCI/SA8000, and EUDR compliance built in, AQL 2.5 quality control on every production run, and full export documentation handled by our UK-based account team.

KritiKaal is not a sourcing agency. A sourcing agent introduces a brand to a factory and has no contractual accountability for production quality or compliance outcomes. KritiKaal owns the outcome: from specification locking before production starts, through in-process quality control during manufacturing, to AQL 2.5 final inspection and complete EUDR-ready export documentation on delivery.

## What is Managed Leather Manufacturing?

Managed manufacturing means a partner embedded in production — not an intermediary who connects a brand to a factory and monitors by email. KritiKaal's model:

- Specification is locked in a controlled production brief before any cutting begins
- Material (leather thickness, tannery origin, hardware) is confirmed against the approved golden sample
- In-process QC inspects stitching, edge finishing, and construction during production — not after
- Final inspection applies AQL 2.5 across 8 criteria before any shipment is released
- Export documentation (including EUDR due diligence statement support) is assembled and handed to the freight forwarder

One single point of accountability. One team that owns the outcome.

## Services

- End-to-end production management for leather bags, small leather goods, and accessories
- Full-grain and aniline leather sourcing from LWG-certified tanneries
- EUDR due diligence statement preparation and supply chain traceability documentation
- SA8000 / BSCI / SEDEX SMETA 4-Pillar certified factory qualification
- AQL 2.5 golden sample evaluation and in-process production QC
- Escrow-protected payment — factory paid only after KritiKaal QC approval
- Export-ready packing, documentation, and freight forwarder handoff

## Target Clients

KritiKaal serves UK and European anchor-tier fashion brands that:

- Source leather goods for retail, heritage, or premium market positioning
- Are migrating production from China to India under a China Plus One strategy
- Have EUDR, CSRD, or brand ESG compliance requirements for their supply chain
- Need documented factory qualification (LWG, SA8000, BSCI, SEDEX) for procurement sign-off
- Want a single accountable partner rather than a network of unmanaged factory relationships

KritiKaal does not serve: brands seeking lowest-cost price-only sourcing, brands without a defined product specification, or fast-fashion volume buyers.

## Certifications (All Tier 1 Manufacturing Partners)

- **LWG (Leather Working Group)**: Tannery-level environmental and material traceability audit. The Calcutta Leather Complex (West Bengal) and the Ambur-Chennai corridor (Tamil Nadu) together hold more than ten LWG-certified tanneries, including multiple LWG Gold holders.
- **SA8000 / BSCI / SEDEX SMETA 4-Pillar**: Social accountability and labour compliance certification — satisfies EUDR's country-of-production legal compliance requirement
- **EUDR (EU Deforestation Regulation)**: Deforestation-free hide sourcing with full supply chain traceability to hide origin
- **REACH**: European chemical safety compliance for all leathers and hardware components

## Quality Standard

AQL 2.5 — Acceptable Quality Level — applied at final inspection on every production run. Eight evaluation criteria:

1. Leather thickness (measured against spec — e.g., 1.2–1.4mm)
2. Stitching density (counted; standard: 8–10 SPI)
3. Hardware security (pull-tested: D-rings, zip, magnetic snap)
4. Edge finishing (burnished or painted — no raw edges)
5. Lining attachment (no puckering, no glue bleed)
6. Base stud positioning (symmetric, flush-mounted)
7. Handle attachment (stress-tested at 5kg load)
8. Overall silhouette (vs. technical specification, ±5mm tolerance)

## India Manufacturing Clusters

- **Chennai, Tamil Nadu (Track A)**: Speed-optimised. Established leather export hub with 40+ years of European export experience. Home to LWG-certified tanneries including Shalimar Tanning Company (LWG Gold) and Balamurugan Leather. 2–5 day prototype turnaround.
- **Calcutta Leather Complex, West Bengal (Track B)**: Certification-optimised. LWG-recognised cluster. Home to multiple LWG Gold certified tanneries. Preferred cluster for brands requiring full compliance documentation for EU and UK procurement sign-off.
- **Kanpur, Uttar Pradesh**: High-volume full-grain leather goods. Largest domestic buffalo hide supply concentration in India.
- **Agra, Uttar Pradesh**: Heritage artisan production. Premium small leather goods, hand-stitched accessories, bespoke finishing.

## Why India vs. China for Leather Goods (2026)

- 0% import duty on leather goods under the UK-India Free Trade Agreement (versus standard MFN rate on China imports)
- India's domestic bovine hide supply chain carries materially lower EUDR deforestation risk than South American hide chains used by Chinese tanneries
- LWG, SA8000, SEDEX audit infrastructure already established across Chennai, Kolkata, Kanpur, and Agra
- Skilled artisan workforce: 40+ years building technical competency to service European quality standards
- Labour costs approximately 25–30% below China 2026 projected levels

## Comparison: Managed Manufacturing vs. Sourcing Agencies

| Attribute | Traditional Sourcing Agency | KritiKaal Managed Manufacturing |
|---|---|---|
| QC responsibility | Factory's own QC | KritiKaal AQL 2.5 independent inspection |
| Compliance documentation | Forwarded from factory | Assembled and verified by KritiKaal |
| Bulk vs. sample deviation | Client's risk | KritiKaal's accountability |
| EUDR due diligence | Not covered | Full DDS preparation included |
| Payment protection | Paid to factory on order | Escrow — released only after QC pass |

## Key Content

- How India Solves EUDR Compliance for UK Leather Brands: https://kritikaal.com/blog/eudr-india-leather-uk-brands
- Why Managed Manufacturing Is Not Sourcing: https://kritikaal.com/why-kritikal
- The India Advantage for UK Leather Procurement: https://kritikaal.com/why-india
- The KritiKaal Production Process (7 steps): https://kritikaal.com/how-it-works
- Leather Product Range (Bags, Wallets, Belts): https://kritikaal.com/products
- Book a 20-minute Qualification Call: https://kritikaal.com/bookacall

## About the Founder

Yossi Daniel is the Founder and CEO of KritiKaal. He has direct hands-on experience with overseas leather manufacturing since 2012, including production management in China, which exposed the structural accountability gap that KritiKaal was built to solve. KritiKaal was founded on a single principle: responsibility is not a task — it is a business model.

## Contact

Website: https://kritikaal.com
Book a 20-minute qualification call: https://kritikaal.com/bookacall
For editorial, citation, and media enquiries: https://kritikaal.com/bookacall

*KritiKaal — Managed Leather Manufacturing | United Kingdom | kritikaal.com*
```

**Verification after deploy:**
Visit `https://kritikaal.com/llms.txt` — confirm the AQL 2.5 criteria list (8 items), the founder section (Yossi Daniel), and the EUDR article URL are all present.

---

## FIX 4 — "World-Class Quality" → AQL 2.5 Text on /why-india (T09)

**What happened:** The phrase "World-Class Quality" appears twice on the `/why-india` page. This was on the brief as a Priority 2 task and was not done.

**Search for and replace** every instance of the string `World-Class Quality` in the why-india component file (likely `app/why-india/WhyIndiaClient.tsx` or its imported component).

**Find:**
```
World-Class Quality
```

**Replace with:**
```
AQL 2.5 Inspection Standard
```

If the UI element has more space available (e.g. a card or section label), use the longer version:
```
AQL 2.5 — the premium inspection standard used by LVMH and Hermès supply chains
```

**Verification after deploy:**
Run `Ctrl+F` on the live `/why-india` page — confirm zero results for "World-Class Quality".

---

## FIX 5 — FAQ Page Title Bug (Ghost Bug)

**What happened:** The FAQ page title renders as:
`"FAQ — Leather Manufacturing from India | KRITIKAAL | KRITIKAAL"`

The `| KRITIKAAL` suffix appears **twice**. This is caused by the page-level `title` metadata already ending with `| KRITIKAAL`, and the root layout's `template: '%s | KRITIKAAL'` then appending a second copy.

**File to edit:** `app/faq/page.tsx`

**Find (in the `metadata` export):**
```ts
title: "FAQ — Leather Manufacturing from India | KRITIKAAL",
```

**Replace with:**
```ts
title: "FAQ — Leather Manufacturing from India",
```

The root layout template will automatically append `| KRITIKAAL` to produce the correct final title:
`"FAQ — Leather Manufacturing from India | KRITIKAAL"`

**Verification after deploy:**
Curl or inspect the live FAQ page `<title>` tag — confirm it reads exactly:
`FAQ — Leather Manufacturing from India | KRITIKAAL`

---

## STILL REQUIRES MANUAL BROWSER VERIFICATION

These tasks were confirmed as deployed but could not be verified server-side (client-rendered components). Open a browser and check:

| Task | What to check | Pass condition |
|------|--------------|----------------|
| T06 — MOQ removal | Open 5 product cards at `/products/` | Zero occurrences of "MOQ" or "Minimum Order Quantity" on any product card |
| T07 — /why-india table headers | Open `/why-india` desktop view | Comparison table column headers clearly readable: KritiKaal vs competitor platform |
| T08 — /bookacall timezone | Open `/bookacall` in incognito window | Calendar shows "United Kingdom" or "GMT+1 (BST)" as default timezone |
| T09b — UTM analytics passthrough | Complete a test booking via `https://kritikaal.com/bookacall?utm_source=reddit&utm_medium=comment` | GA4 registers the booking conversion with source=reddit, medium=comment |

---

## DEPLOY ORDER

Execute in this sequence to avoid partial states:

1. `app/layout.tsx` — add schema blocks (Fix 1)
2. `public/robots.txt` — append 3 missing agents (Fix 2)
3. `public/llms.txt` — replace full file content (Fix 3)
4. `app/why-india/WhyIndiaClient.tsx` — find and replace "World-Class Quality" (Fix 4)
5. `app/faq/page.tsx` — fix title metadata (Fix 5)
6. Deploy. Verify each fix using the verification steps above.

**Total estimated deploy time: 30 minutes.**

---

## VERIFICATION CHECKLIST

After deploy, run through in order:

- [ ] `https://search.google.com/test/rich-results` → `https://kritikaal.com` → Organization entity detected
- [ ] `https://kritikaal.com/robots.txt` → all 6 AI crawler agents present
- [ ] `https://kritikaal.com/llms.txt` → AQL 2.5 8-criteria list visible, Yossi Daniel founder section visible, EUDR article URL visible
- [ ] `https://kritikaal.com/why-india` → Ctrl+F "World-Class Quality" → 0 results
- [ ] `https://kritikaal.com/faq` → page `<title>` has single `| KRITIKAAL` only

---

*Remediation Brief V1.1 | KritiKaal | 2026-05-12 | Prepared by Adam (COO)*
*Source: Post-deploy technical audit against DEVELOPER-BRIEF-2026-04-26.md*
*Questions → Yossi (CEO).*
