# KRITIKAAL Backend API

Backend service for handling booking requests and email notifications using Resend.

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
  # KRITIKAAL — Backend API

  This repository contains the backend service used by the KRITIKAAL frontend. It handles booking submissions from the website and sends confirmation and admin notification emails using Resend.

  ## Table of contents

  - [Quickstart](#quickstart)
  - [Configuration](#configuration)
  - [Scripts](#scripts)
  - [API](#api)
  - [Email flow (Resend)](#email-flow-resend)
  - [Project layout](#project-layout)
  - [Deployment notes](#deployment-notes)
  - [Troubleshooting](#troubleshooting)
  - [Security & best practices](#security--best-practices)

  ---

  ## Quickstart

  Requirements:

  - Node.js 18+ (recommended)
  - npm

  Install and run locally:

  ```bash
  cd backend
  npm install
  npm run dev
  ```

  Open `http://localhost:5000/health` to verify the server is running (adjust port via `.env`).

  ---

  ## Configuration

  Copy the environment template and provide real values:

  ```bash
  cd backend
  cp .env.example .env
  ```

  Minimum environment variables (example):

  ```env
  RESEND_API_KEY=re_your_api_key_here
  FROM_EMAIL=bookings@yourdomain.com
  ADMIN_EMAIL=you@yourdomain.com
  PORT=5000
  ```

  Notes:

  - Resend free accounts can only send emails to verified addresses — verify your domain for production use.
  - Never commit `.env` to the repository.

  ---

  ## Scripts

  - `npm run dev` — start development server with auto-reload
  - `npm start` — start production server
  - `npm test` — run tests (if present)

  ---

  ## API

  ### POST /api/book-call

  Submit a booking request. The backend sends a confirmation email to the user; if the user confirms, an admin notification is sent.

  Example request body:

  ```json
  {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+911234567890",
    "preferredDate": "2026-02-20",
    "message": "Notes about the booking"
  }
  ```

  Success response example:

  ```json
  { "success": true, "message": "Booking request submitted successfully." }
  ```

  ### GET /health

  Lightweight health check endpoint. Returns server status.

  ---

  ## Email flow (Resend)

  1. User submits booking via frontend → backend sends confirmation email to the user (Resend).
  2. User clicks confirmation link → backend confirms and sends admin notification to `ADMIN_EMAIL`.

  If testing on a Resend free account, use verified recipients only or verify your sending domain.

  ---

  ## Project layout

  ```
  backend/
  ├─ controllers/
  │  └─ bookingController.js    # booking handling logic
  ├─ routes/
  │  └─ booking.js              # express routes
  ├─ services/
  │  └─ emailService.js         # Resend integration & templates
  ├─ .env.example
  ├─ package.json
  └─ server.js
  ```

  ---

  ## Deployment notes

  - Set `RESEND_API_KEY`, `FROM_EMAIL`, and `ADMIN_EMAIL` in your production environment.
  - For Docker usage, ensure environment variables are passed at runtime (or via secrets).

  Example Docker commands:

  ```bash
  docker build -t KRITIKAAL-backend ./backend
  docker run -e RESEND_API_KEY=re_xxx -e FROM_EMAIL=bookings@domain -e ADMIN_EMAIL=you@domain -p 5000:5000 KRITIKAAL-backend
  ```

  ---

  ## Troubleshooting

  - Server does not start: check Node version, port conflicts, and `server.js` error logs.
  - Emails not sending: confirm `RESEND_API_KEY` and domain verification status in Resend.
  - CORS errors: ensure your frontend origin is whitelisted in backend CORS configuration.

  ---

  ## Security & best practices

  - Never commit secrets or `.env` into source control.
  - Rotate API keys if suspected compromised.
  - Validate and sanitize incoming request data.

  ---

  If you want, I can add example curl commands, a Postman collection, or a GitHub Actions workflow to run tests and deploy. Tell me which and I'll add it.

