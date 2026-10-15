# Presentation — AI-Assisted Skin Screening for Rural PHCs

## 1. Problem

Rural PHCs in Dakshina Kannada & Udupi (coastal Karnataka) handle thousands of
skin complaints a month with **no dermatologist on site**. Suspected melanomas
and other serious lesions travel up the referral chain by guesswork: some
referred too late, many not referred at all. Result — avoidable diagnostic
delays for exactly the patients least able to travel.

## 2. Solution

A screening aid that fits the PHC's existing workflow:

1. PHC staff register the patient and record **consent** (30 seconds).
2. Upload a phone photo — the ResNet50 model classifies it into 7 lesion
   classes and aggregates them into a **LOW / MEDIUM / HIGH** risk level with
   confidence scores.
3. The UI shows a colorblind-safe risk badge, plain-language recommendation
   ("Refer IMMEDIATELY" for HIGH), and one-tap referral with urgency +
   follow-up date.
4. Every step is audited; PHC-level dashboards surface referral rate and
   high-risk counts for the district health office.

## 3. Impact

- **Projected ~60% reduction in diagnostic delays** for referred serious
  lesions (target; to be validated in a pilot — the tool's job is to make
  the referral decision *explicit* and *immediate* for HIGH-risk screens).
- **Zero training needed** — the UI is built for non-clinicians: large touch
  targets, jargon-free language, disclaimer always visible.
- **Open source + affordable** — runs inference on a basic laptop CPU
  (no GPU), public dataset, MIT license. Deployable to 100+ PHCs.

## 4. Tech

- **Model:** ResNet50 (ImageNet transfer) + custom head, trained on HAM10000
  (10,015 dermatoscopic images, 7 classes); risk buckets = fixed clinical
  mapping of classes; class-weighted loss to minimize dangerous false
  negatives. `ml/metrics.json` reports measured accuracy / per-class
  precision-recall-F1 / confusion matrix for the actual trained run.
- **Backend:** Flask + SQLAlchemy (SQLite dev / PostgreSQL prod), JWT auth,
  rate limiting, consent enforcement, audit log, hash-named image storage
  (no PII in filenames).
- **Frontend:** React 18 + Vite + Tailwind + Recharts; offline-tolerant
  intake drafts; authenticated image streaming.
- **Deployment:** `docker compose up` — Flask, PostgreSQL, nginx/React.

## 5. Demo (3-minute walkthrough)

1. Register staff → disclaimer acknowledgement (compliance by design).
2. Intake → consent checkboxes → patient ID.
3. Upload image → spinner ("Analyzing… 3–5 seconds") → **result screen**:
   risk badge + confidence bars + recommendation.
4. Refer to specialist → referral ID → history row updates.
5. Dashboard: totals, referral rate, 7/30/90-day trend, risk pie, top conditions.
6. Show `python -m pytest -q` → 26 passing tests.

*(Without trained weights the API runs in flagged DEMO mode — same workflow,
deterministic placeholder scores. Training instructions are in SETUP.md.)*

## 6. Future Work

- Multi-condition support: **fungal infections, eczema, psoriasis** (needs
  labelled images; HAM10000 covers only the 7 lesion classes)
- Android app with offline capture + sync
- SMS follow-up reminders (outcome tracking is already in the schema)
- Active-learning loop: dermatologist outcomes feed model retraining
- Kannada/Tulu localization of the UI
