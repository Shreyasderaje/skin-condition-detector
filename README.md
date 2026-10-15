# Skin Condition Detector for Rural PHCs

AI-assisted **screening** tool that helps Primary Health Center (PHC) staff in
coastal Karnataka triage skin conditions — without an on-site dermatologist.
Staff upload a skin photo, the model estimates a **LOW / MEDIUM / HIGH** risk
level with confidence scores, and the system drives consent, referrals,
follow-up and audit trails.

> ⚠️ **This tool is NOT a diagnosis device.** It is a decision-support aid.
> All HIGH risk cases must be seen by a dermatologist. Consult a qualified
> physician for final diagnosis and treatment.

## Features

- **Image upload & ML inference** — ResNet50 (PyTorch) with a deterministic
  demo-model fallback so the full product runs before training
- **Risk categorization** — 7 HAM10000 lesion classes aggregated into
  LOW / MEDIUM / HIGH with per-bucket confidence
- **Referral management** — reason, specialist, urgency, follow-up date, outcome
- **Consultation history & analytics** — filters, CSV export, trends, risk
  distribution, condition breakdown
- **Compliance built in** — patient consent records, medical disclaimer API,
  append-only audit log, PHC-scoped data isolation
- **JWT auth** — bcrypt-style password hashing, 24h tokens, rate limiting
- **One-command deployment** — `docker-compose up` (Flask + PostgreSQL + nginx/React)

## Quick Start (Local Development)

```bash
# 1. Backend  (http://localhost:5000)
cd backend
pip install -r requirements.txt          # core stack — runs without PyTorch
cp .env.template .env
python app.py

# 2. Frontend (http://localhost:3000) — new terminal
cd frontend
npm install
npm start
```

Open http://localhost:3000, register a PHC staff account, create a patient,
and upload `sample_images/sample_1.jpg`. Until you train the model (below),
results come from the **demo model** and every response/UI carries a
"Demo model" flag — the workflow is identical, the weights just aren't real yet.

Optional: seed a ready-made demo account + sample consultations:

```bash
cd backend && python seed_demo.py       # login: demo@phc.in / Demo@12345
```

## Quick Start (Docker)

```bash
docker compose up --build
# frontend: http://localhost:3000  (nginx proxies /api -> backend)
# backend:  http://localhost:5000
# database: PostgreSQL 16 (volume: postgres_data)
```

## Running the Tests

```bash
cd backend
pip install pytest   # (or: pip install -r requirements.txt pytest)
python -m pytest -q  # 26 tests: auth, patients, consultations, analytics, compliance
```

## Training the Real Model

HAM10000 provides the 7 lesion classes; see `backend/ml/dataset_info.txt`.

```bash
cd backend
pip install -r requirements-ml.txt                       # torch CPU is enough for inference
python ml/prepare_data.py --metadata HAM10000_metadata.csv \
    --images <ham10000 image dir> --out ../data/skin      # stratified 70/15/15 split
python -m ml.train --data-dir ../data/skin --epochs 30    # -> ml/model.pth + ml/metrics.json
python ml/export_onnx.py                                  # optional ONNX export
```

`ml/train.py` uses ImageNet-pretrained ResNet50 with the spec'd head
(Dropout 0.5 → 256 ReLU → classes), class-weighted cross-entropy, early
stopping on validation loss, and writes test accuracy, per-class
precision/recall/F1 and the confusion matrix to `ml/metrics.json`.
**Accuracy depends on your training run — report the numbers from
metrics.json, not from this README.** Restart the API afterwards and the
backend picks up `ml/model.pth` automatically (mode changes from `demo`
to `torch`/`onnx`).

## API Documentation

Base URL `/api`. Authenticated endpoints need `Authorization: Bearer <token>`.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Create staff account → access token | — |
| POST | `/auth/login` | Login → access token | — |
| POST | `/auth/logout` | Logout (audited) | ✓ |
| POST | `/patients` | Register patient | ✓ |
| GET | `/patients` | List patients (`?page&limit`) | ✓ |
| GET | `/patients/{id}` | Patient detail | ✓ |
| POST | `/consultations/upload` | Multipart image + patient_id (+vitals_temp) → risk result | ✓ |
| GET | `/consultations` | History (`?patient_id&risk_level&start_date&end_date&page&limit`) | ✓ |
| GET | `/consultations/{id}` | Full consultation incl. patient | ✓ |
| GET | `/consultations/{id}/image` | Stored image (JPEG) | ✓ |
| PATCH | `/consultations/{id}/notes` | Add staff notes | ✓ |
| POST | `/consultations/{id}/referral` | Create referral (reason/urgency/specialist/date) | ✓ |
| PATCH | `/consultations/{id}/outcome` | Set follow-up outcome (healed/ongoing/escalated) | ✓ |
| GET | `/analytics/summary` | Totals, risk distribution, referral rate, conditions | ✓ |
| GET | `/analytics/trends` | `?period=7days\|30days\|90days` daily counts | ✓ |
| GET | `/disclaimer` | Medical disclaimer text + version | — |
| POST | `/consent` | Record patient consent | ✓ |
| GET | `/health` | Liveness probe (no /api prefix) | — |

Errors are JSON `{"error": "..."}` with status 400 (invalid input), 401
(no/invalid token), 403 (no consent / forbidden), 404 (not found), 409
(duplicate email), 413 (image > 5MB), 429 (rate limit 30 req/min), 500
(includes an `error_id` for log correlation).

## Dataset

- **HAM10000** — 10,015 dermatoscopic images, 7 classes:
  <https://www.kaggle.com/datasets/kmader/skin-cancer-mnist-ham10000>
- **ISIC Archive** (optional extra validation): <https://www.isic-archive.com/>

## Model

- ResNet50 (ImageNet-pretrained), head: Dropout(0.5) → Dense(256)+ReLU → Dense(7)
- Risk buckets are the fixed clinical mapping of the 7 classes
  (see `backend/ml/dataset_info.txt`); bucket confidence = summed class probabilities
- Images: 224×224, ImageNet normalization, ±20° rotation / flip / brightness augmentation
- **Scope note:** HAM10000 contains no fungal/eczema/psoriasis images; the API
  reports the detected lesion class from the 7 available categories. Adding
  rural-relevant conditions (fungal, eczema, psoriasis) is future work needing
  labelled data.

## Medical Disclaimer

> ⚠️ This tool is NOT a diagnosis device. It is a screening aid only.
> All HIGH risk cases must be seen by a dermatologist. A LOW/MEDIUM result
> does not rule out a serious condition. Consult a qualified physician for
> final diagnosis and treatment.

Served by `GET /api/disclaimer`, displayed on every results screen, and
acknowledged at registration.

## Deployment Checklist

- [ ] `DATABASE_URL` → production PostgreSQL
- [ ] `JWT_SECRET` → long random string
- [ ] HTTPS enabled (reverse proxy / load balancer)
- [ ] Image storage volume mounted (or swap `utils/image_handler.py` for S3)
- [ ] Error logging wired (e.g. Sentry hook in `app.errorhandler`)
- [ ] Load test (50+ concurrent users; gunicorn workers sized accordingly)
- [ ] Trained `model.pth` mounted and `mode != demo` verified

## Project Structure

```
skin-condition-detector/
├── backend/
│   ├── app.py                 # Flask entry point (create_app factory)
│   ├── config.py              # env-driven configuration
│   ├── models/                # SQLAlchemy: phc_staff, patients, consultations, audit_logs, consents
│   ├── routes/                # auth, patients, consultations, analytics, compliance
│   ├── ml/                    # preprocessing, inference (torch/onnx/demo), train.py, prepare_data.py, export_onnx.py
│   ├── utils/                 # jwt, auth, validators, image storage, audit, rate limiter
│   ├── tests/                 # pytest suite (26 tests)
│   └── requirements.txt       # + requirements-ml.txt (torch/torchvision/onnx)
├── frontend/
│   ├── src/pages/             # Login, PatientIntake, ImageUpload, Results,
│   │                          # ReferralForm, ConsultationHistory, Dashboard, Disclaimer
│   ├── src/components/        # RiskBadge, ConfidenceChart, Header, Footer, RequireAuth, DisclaimerBanner
│   ├── src/services/api.js    # Axios instance + interceptors + authenticated image fetch
│   └── Dockerfile.frontend    # node build -> nginx (proxies /api)
├── scripts/make_sample_images.py
├── sample_images/             # synthetic smoke-test images (not medical data)
├── docker-compose.yml         # backend + postgres + frontend
├── Dockerfile                 # backend
├── README.md / SETUP.md / PRESENTATION.md
```

## Contributing

Fork → create a feature branch → `python -m pytest` + `npm run build` green →
submit a PR.

## License

MIT
