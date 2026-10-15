# How to Run This Project (Judges & Reviewers)

Two supported paths: **local development** (fastest, SQLite) or **Docker**
(one command, PostgreSQL). Both give the same UI and API. A prebuilt demo
account is available via the seeder.

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js 18+
- *(Docker path only)* Docker + Docker Compose
- *(Real model training only)* `requirements-ml.txt` installed; CPU is enough

---

## Option A — Local Development

### Step 1: Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.template .env          # defaults are fine for the demo
python app.py
```

Server runs on http://localhost:5000 — verify with `curl http://localhost:5000/health`.

> The first upload logs
> `PyTorch model unavailable ... falling back to demo model`. That is
> expected: without trained weights the API uses a clearly-flagged
> deterministic demo model so the entire workflow is testable.

### Step 2: Frontend (new terminal)

```bash
cd frontend
npm install
npm start
```

App runs on http://localhost:3000 (Vite proxies `/api` to the backend).

### Step 3: Walkthrough

1. Register at http://localhost:3000 (tick the disclaimer acknowledgement).
2. **New Patient** → fill intake + both consents → **Next**.
3. Upload an image (drag & drop or browse) → **Start Screening**.
4. See the risk badge, confidence bars, condition suggestion, recommendation.
5. **Refer to Specialist** → pick reason/urgency/date → submit.
6. **History** → open the row → full detail view; **Export CSV** works.
7. **Dashboard** (`/`) → totals, referral rate, trends, risk pie.

Sample images: use `sample_images/sample_1.jpg` … `sample_3.jpg`
(synthetic placeholders for pipeline testing) or real HAM10000 test-set
images from <https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000>.

One-command demo data (idempotent):

```bash
cd backend && python seed_demo.py
# login with demo@phc.in / Demo@12345 (Mulki PHC)
```

---

## Option B — Docker (one command)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000 (nginx serves the React build, proxies `/api`)
- Backend:  http://localhost:5000
- DB:       PostgreSQL 16 with a named volume

To enable **real inference** in Docker after training:

```bash
cd backend && pip install -r requirements-ml.txt
python ml/prepare_data.py --metadata HAM10000_metadata.csv --images <dir> --out ../data/skin
python -m ml.train --data-dir ../data/skin --epochs 30
# then uncomment the model mount in docker-compose.yml and:
docker compose up --build
```

---

## API Testing (curl)

```bash
# 1. Register / login
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@phc.in","password":"Demo@12345"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. Upload a skin image for screening
curl -s -X POST http://localhost:5000/api/consultations/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@sample_images/sample_1.jpg;type=image/jpeg" \
  -F "patient_id=1" -F "vitals_temp=37.2"

# 3. Analytics
curl -s "http://localhost:5000/api/analytics/summary" -H "Authorization: Bearer $TOKEN"
```

## Running the Test Suite

```bash
cd backend && pip install pytest && python -m pytest -q
# 26 passed — covers auth, patient CRUD + PHC isolation, upload/consent rules,
# referral/outcome, analytics, disclaimer
```

## Staff Usage Guidelines (per compliance section of the spec)

- Always record patient consent **before** uploading (the upload endpoint
  enforces it — you'll get a 403 without it).
- Treat results as *screening suggestions*. HIGH ⇒ refer immediately;
  MEDIUM ⇒ refer within 2 weeks; LOW ⇒ routine follow-up. When in doubt,
  refer.
- Never rely on the tool for a final diagnosis; document findings in
  **Staff Notes**.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Address already in use` on 5000 | `PORT=5001 python app.py` and set the proxy in `frontend/vite.config.js` |
| 401 on every API call after a while | JWT expired (24h) — log in again |
| Upload returns 403 | Consent missing — re-run intake or `POST /api/consent` |
| Upload returns 413 | Image > 5MB — compress or raise `MAX_IMAGE_MB` |
| 429 Too Many Requests | Rate limit is 30 req/min/IP — wait or raise `RATE_LIMIT_PER_MINUTE` |
| Frontend can't reach backend | Ensure backend is on :5000 (dev proxy) or `VITE_API_BASE_URL` set |
