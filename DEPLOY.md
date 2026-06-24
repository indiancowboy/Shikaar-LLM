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

## Local dev (unchanged)

```bash
# backend
cd backend && ./venv/bin/uvicorn app.main:app --reload      # no password locally
# frontend
cd frontend && cp .env.local.example .env.local && npm run dev
```
