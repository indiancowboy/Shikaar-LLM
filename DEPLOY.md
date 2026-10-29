# Deploying Shikaar (demo stack)

Goal: a shareable URL for a few people, protected by a shared password so the
OpenAI/Pinecone bill stays sane. Stack: **Render** (FastAPI backend) + **Vercel**
(Next.js frontend). Both have free tiers.

Knowledge base note: the recipes/cuisines/techniques are already embedded in your
**Pinecone** cloud index, so the deployed backend just connects to it — no need to
re-ingest on deploy.

---

## 1. Backend → Render

1. Push to GitHub (done). In [Render](https://render.com): **New → Blueprint**,
   select this repo. Render reads `render.yaml` and creates the `shikaar-api` web
   service (root dir `backend`, start `uvicorn app.main:app`).
2. Set the secret env vars in the service's **Environment** tab (these are
   `sync:false` in the blueprint, so Render won't read them from the file):
   - `OPENAI_API_KEY` — your OpenAI key
   - `PINECONE_API_KEY` — your Pinecone key
   - `PINECONE_HOST` — your Pinecone host
   - `SHIKAAR_ACCESS_PASSWORD` — **pick a password** to share with your testers
3. Deploy. When it's live, grab the URL, e.g. `https://shikaar-api.onrender.com`.
   Verify: `https://shikaar-api.onrender.com/health` → `{"status":"ok"}`.

> Free tier sleeps after ~15 min idle → first request after that takes ~30s to
> wake. Inventory (SQLite) resets on restart/redeploy — expected for a demo. To
> make inventory durable later, add a Render Disk or move to Postgres.

## 2. Frontend → Vercel

1. In [Vercel](https://vercel.com): **Add New → Project**, import this repo.
2. Set **Root Directory = `frontend`** (Vercel auto-detects Next.js).
3. Add an environment variable:
   - `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g.
     `https://shikaar-api.onrender.com`, no trailing slash)
4. Deploy. You'll get a URL like `https://shikaar.vercel.app`.

## 3. Try it

Open the Vercel URL → you'll get a **password prompt** → enter
`SHIKAAR_ACCESS_PASSWORD`. It's validated server-side and stored in your browser
(never baked into the public bundle). Share the URL + password with your testers.

---

## How the gate works

- Backend: if `SHIKAAR_ACCESS_PASSWORD` is set, `/ask`, `/freezer/*`, and `/fish/*`
  require an `X-Access-Password` header matching it (401 otherwise). `/health`
  stays open. If the env var is **unset** (local dev), the gate is a no-op.
- Frontend: `components/Gate.tsx` prompts for the password, validates it against
  `/auth/check`, and stores it in `localStorage`; `lib/api.ts` sends it on every
  request.

This is a speed bump for a small demo, not real auth. For real users, add proper
accounts/sessions (and rate limiting) later.

## Accounts mode (real sign-in + durable freezers)

The demo above is per-browser (freezers vanish when the browser is cleared) and
SQLite-backed (freezers reset on every Render redeploy). To make freezers belong
to real **users** and persist across devices and deploys, switch to accounts
mode. It's all env-gated — set the vars and redeploy; set nothing and the demo
behaves exactly as before.

Provider: **Supabase** gives both the sign-in (JWT) and the Postgres database on
one free project.

### 1. Create the Supabase project

1. New project at https://supabase.com. Pick a region near your users.
2. **Project Settings → API**: copy the **Project URL** and the publishable /
   anon key (`sb_publishable_...` on new projects). No JWT secret is needed — new
   projects sign tokens with asymmetric ES256 keys and the backend verifies them
   via the project's public JWKS endpoint (derived from the Project URL).
   *(Only older projects that still use a legacy HS256 "JWT Secret" set
   `SUPABASE_JWT_SECRET` instead — see the note below.)*
3. **Project Settings → Database → Connection string**: copy the **Session
   pooler** URI (`postgresql://postgres.<ref>:<password>@...pooler.supabase.com:5432/postgres`).
   The backend creates its `freezer_items` table automatically on first request.
4. **Authentication → Providers**: email is on by default (magic link). To offer
   Google, enable the Google provider and add your OAuth client id/secret.
5. **Authentication → URL Configuration**: add your Vercel URL to **Redirect
   URLs** so magic-link / Google sign-in returns to the app.

### 2. Backend (Render) env

Set these on the `shikaar-api` service and **remove** `SHIKAAR_ACCESS_PASSWORD`
(the token is the gate now):

- `SUPABASE_URL` — your Project URL, e.g. `https://<project-ref>.supabase.co`
  (the backend fetches the JWKS from here to verify ES256 tokens)
- `DATABASE_URL` — the Session pooler URI from step 3

With `SUPABASE_URL` set, every `/ask`, `/freezer/*`, `/fish/*` request must carry
a valid Supabase token (401 otherwise), and inventory is stored in Postgres keyed
by the user id — so it's durable and private per user.

> **Legacy projects only:** if your project still signs tokens with the old HS256
> **JWT Secret** (Project Settings → API → JWT Settings), set
> `SUPABASE_JWT_SECRET` to that secret instead of (or in addition to)
> `SUPABASE_URL`. The backend verifies whichever algorithm the token declares.

### 3. Frontend (Vercel) env

- `NEXT_PUBLIC_SUPABASE_URL` — the Project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — the anon public key

Redeploy. The app now shows a Google / magic-link sign-in instead of the shared
password, and a user's freezer follows them across phone and laptop.

> Rollback is trivial: unset the three `SUPABASE_*`/`DATABASE_URL` vars (and
> restore `SHIKAAR_ACCESS_PASSWORD`) to drop back to the demo.

## AI usage limit

Each user gets **20 AI actions per day** (Parse it, Photo, Plan my week, and
`/ask`); the 21st gets a friendly "you've used today's AI actions" message.
Adding items by hand, Used 1, Estimate cuts and Cook First never count.
Counts live in the `ai_usage` table next to the freezer and reset each UTC day.

Change it with `AI_DAILY_LIMIT` on the Render service (e.g. `50`), or set it to
`0` to turn the limit off. No redeploy of code needed, just save the variable.

## Local dev (unchanged)

```bash
# backend
cd backend && ./venv/bin/uvicorn app.main:app --reload      # no password locally
# frontend
cd frontend && cp .env.local.example .env.local && npm run dev
```
