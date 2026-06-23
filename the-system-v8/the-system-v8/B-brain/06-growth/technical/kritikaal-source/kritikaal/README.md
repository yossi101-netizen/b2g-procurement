# KRITIKAAL

KRITIKAAL is a marketing + product site and lightweight backend for a precision leather manufacturing business. This repository contains the frontend (Vite + React + TypeScript) and a small backend (Express) that handles booking requests and sends emails.

This README describes how to run the project locally, where the important pieces are, and how to configure environment variables for development and production.

Table of contents
- [Quickstart](#quickstart)
- [Repository structure](#repository-structure)
- [Frontend details](#frontend-details)
- [Backend details](#backend-details)
- [Environment variables](#environment-variables)
- [Running locally](#running-locally)
- [Build & deploy](#build--deploy)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Quickstart

Requirements:

- Node.js 18+ (recommended)
- npm (or pnpm / yarn)

Install dependencies for both frontend and backend and run the dev servers:

```bash
# from repo root
npm install

# run frontend dev server (vite)
npm run dev

# in a separate shell, run backend server
cd backend
npm install
npm run dev
```

Open the frontend at the Vite dev URL (usually `http://localhost:5173`) and the backend health endpoint at `http://localhost:5000/health`.

---

## Repository structure

Top-level layout:

```
.
├─ backend/                 # Node/Express backend (booking + email)
├─ public/                  # static assets served by frontend
├─ src/                     # frontend source (React + TS)
├─ package.json             # top-level scripts and dev tooling
├─ README.md                # this file
└─ ...
```

See `backend/README.md` for details specific to the backend service.

---

## Frontend details

- Built with Vite + React + TypeScript
- UI uses Tailwind CSS and custom design tokens
- Pages are in `src/pages/` (e.g. `WhyIndia.tsx`, `HowItWorks.tsx`)
- Reusable components are in `src/components/`
- Translations are in `src/translations/`

Common commands (from repo root):

```bash
npm run dev      # start Vite dev server
npm run build    # build production assets
npm run preview  # preview production build locally
```

---

## Backend details

See `backend/README.md` for full backend documentation. In short:

- Lightweight Express server in `backend/`
- Handles booking requests and sends confirmation/admin emails via Resend
- Dev script: `cd backend && npm run dev`

If you need quick reference: backend health is at `/health` and booking endpoint is `/api/book-call`.

---

## Environment variables

- Frontend may reference public environment values in `.env` (Vite conventions)
- Backend requires a `.env` with keys such as `RESEND_API_KEY`, `FROM_EMAIL`, `ADMIN_EMAIL`, and `PORT` — see `backend/.env.example` and `backend/README.md` for details.

---

## Running locally

1. Install dependencies

```bash
npm install
cd backend && npm install
```

2. Start frontend (from repo root):

```bash
npm run dev
```

3. Start backend (from `backend/`):

```bash
cd backend
npm run dev
```

4. Open the dev URL shown by Vite (usually `http://localhost:5173`).

---

## Build & deploy

Build the frontend for production:

```bash
npm run build
```

Deployables:

- `dist/` contains the frontend static assets after `npm run build`.
- Backend can be deployed to any Node host; ensure environment variables are provided and that the sending domain is verified with Resend.

Simple Docker workflow (idea): build frontend assets, copy into a small web server or upload to your CDN, deploy backend as a Node service.

---

## Troubleshooting

- If the frontend can't reach the backend, ensure backend is running and CORS is configured correctly.
- If emails fail in backend, verify `RESEND_API_KEY` and domain verification in Resend.
- If the dev server errors on startup, check Node version and run `npm ci` to ensure a clean install.

---

## Contributing

If you plan to contribute:

1. Create a branch from `main` (or `mobile_responsiveness` if working on mobile fixes)
2. Run and test both frontend and backend locally
3. Open a PR with a clear description of changes

---

If you want, I can also:

- Add a developer script to start frontend + backend with a single command
- Add example curl/Postman requests or a Postman collection
- Add GitHub Actions for lint/test/build

Tell me which and I'll add it.
