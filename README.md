# 🛡️ ElderLife AI — Autonomous Elderly Safety & Predictive Care Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-TCN_Fall_Net-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/React-18_+_Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose_Stack-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Privacy-First Multimodal AI Telemetry, Temporal Fall Detection, Explainable Risk Scoring & Automated Care Escalation.**

</div>

---

## 1. Executive Summary & Architectural Vision

**ElderLife AI** is an end-to-end, containerized clinical-grade safety and behavioral monitoring platform engineered for older adults living independently. Unlike conventional reactive alarm systems that rely on manual button presses or rigid threshold rules, ElderLife AI fuses **spatiotemporal computer vision**, **wearable accelerometer telemetry**, and **personalized behavioral baselines** into a deterministic, explainable risk-scoring engine.

### Core Engineering Pillars
* **Privacy-by-Design Telemetry:** Zero raw video or imagery is ever persisted to disk or transmitted across the network. Edge vision pipelines extract skeletal keypoints (`MediaPipe`) and motion vectors (`OpenCV`), transmitting only anonymized mathematical tensors and confidence scores.
* **Temporal Deep Learning (`fall_detection/`):** Replaces static frame-by-frame heuristics with a lightweight **Temporal Convolutional Network (TCN)** (`24,641` parameters, `0.1 MB`) trained on real-world **URFD** sequences, capturing the complete kinematic trajectory (*standing $\rightarrow$ rapid descent $\rightarrow$ floor immobilization*) with **F1 = 0.951** and **AUC = 0.992**.
* **Explainable Hybrid Risk Engine (`XAI`):** Combines learned risk classifiers with hard clinical safety floors, attaching human-readable causal attributions (*"Why?"*) to every risk elevation.
* **Stateful Alert Escalation Machine:** Prevents alarm fatigue through confidence gating, a 60-second resident verification window, debounced multi-stage escalation (`Resident Prompt $\rightarrow$ Caregiver Alert $\rightarrow$ Emergency Escalation`), and 30-minute post-acknowledgement snooze windows.
* **Full Bilingual Localization (EN / AR):** Native Right-to-Left (RTL) layout switching and dynamic `Accept-Language` API resolution storing parameterized message keys rather than static strings.

---

## 2. System Architecture & Data Flow

```text
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                 EDGE & SENSOR INGESTION                              │
│  [Fixed RGB Camera] ──► OpenCV Motion + MediaPipe Pose (IMAGE Mode @ 15fps)          │
│                              │                                                       │
│                              ▼                                                       │
│                     Temporal TCN Service (fall_detection/)                           │
│                     • 19-channel kinematic tensor (3.2s window)                      │
│                     • Alert State Machine (Debounce + 30s Cooldown)                  │
│  [Wearable IMU]     ──► Tri-axial Accelerometer Windowing                            │
│  [Resident Tablet]  ──► Dedicated Senior UI (#/elder via 6-digit X-Elder-Code)       │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ HTTPS / JSON (X-Device-Key / Bearer)
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         CORE ORCHESTRATION BACKEND (FastAPI)                         │
│  ┌─────────────────────┐   ┌──────────────────────┐   ┌───────────────────────────┐  │
│  │  Ingestion & Auth   │──►│  Hybrid Risk Engine  │──►│ Escalation & Notification │  │
│  │  • RBAC (Admin/CG)  │   │  • Personal Baseline │   │ • Verification Timers     │  │
│  │  • Login Throttling │   │  • Causal "Why?" XAI │   │ • Telegram & SMTP Dispatch│  │
│  └─────────────────────┘   └──────────────────────┘   └───────────────────────────┘  │
│                                          │                                           │
│                                          ▼                                           │
│                         PostgreSQL 16 + Alembic Migrations                           │
└──────────────────────────────────────────┬───────────────────────────────────────────┘
                                           │ REST API + Bilingual i18n
                       ┌───────────────────┴───────────────────┐
                       ▼                                       ▼
┌─────────────────────────────────────────────┐ ┌──────────────────────────────────────┐
│     COMMAND CENTER UI (React + Nginx)       │ │    ENTERPRISE BI & ANALYTICS         │
│  • Real-time Safety Overview & Risk Matrix  │ │  • Star-Schema CSV Exports           │
│  • Resident Timelines & Care Plan Checklists│ │  • Power Query (M) & DAX Measures    │
│  • Alert Triage & Acknowledgement Workflow  │ │  • Longitudinal Cohort Reporting     │
└─────────────────────────────────────────────┘ └──────────────────────────────────────┘

```

---

## 3. Repository Blueprint

| Module | Architectural Responsibility | Key Artifacts |
| --- | --- | --- |
| **`backend/`** | Production FastAPI service, RBAC security, SQLAlchemy ORM, Alembic schema migrations, hybrid risk scoring, and background escalation scheduler. | `app/api/`, `app/services/risk_service.py`, `app/i18n.py`, `alembic/` |
| **`fall_detection/`** | Dedicated Temporal Deep Learning microservice & research suite for vision-based fall detection with full ablation benchmarks and interactive HTML reporting. | `models/fall_tcn.pt`, `src/models/temporal.py`, `src/inference/alerting.py`, `reports/showcase.html` |
| **`frontend/`** | Responsive React 18 SPA served via Nginx; includes Command Center, Caregiver Triage, Admin Console, and simplified Senior Self-Service UI (`#/elder`). | `src/App.jsx`, `src/pages.jsx`, `src/locales/{en,ar}.js` |
| **`ml/`** | Offline ML experimentation lab for SisFall (accelerometer), CASAS (smart-home activity), and synthetic baseline calibration with automated artifact export. | `training/train_*.py`, `preprocessing/`, `export_to_backend.py` |
| **`computer_vision/`** | Real-time webcam/video capture daemon bridging local camera streams to backend pose ingestion endpoints. | `monitor.py`, `pipeline.py` |
| **`power_bi/`** | Complete Business Intelligence semantic layer including Power Query transformations, DAX KPIs, and synthetic star-schema datasets. | `measures.dax`, `power_query.m`, `dashboard_spec.md` |
| **`tests/` & `docs/**` | Unified test runner executing backend, frontend, ML, and CV test suites alongside 15 architectural & evaluation specifications. | `tests/run_all.py`, `docs/ARCHITECTURE.md`, `docs/MODEL_EVALUATION.md` |

---

## 4. Deep Dive: Temporal Fall Detection (`fall_detection/`)

To overcome the high false-positive rates of single-frame posture heuristics, the vision subsystem implements a rigorous, leak-free temporal modeling pipeline evaluated via **5-Fold Event-Level Cross-Validation** on the **UR Fall Detection Dataset (URFD — 70 unique events: 30 falls, 40 ADLs)**:

### Critical Data Engineering Safeguards

1. **Strict Camera-Split Isolation:** Eliminated cross-camera data leakage by isolating `cam0` (`70` unique events) and cropping side-by-side Depth+RGB frames (`640×240` $\rightarrow$ `320×240` RGB) prior to feature extraction.
2. **Stateless Pose Extraction:** Identified anatomical skeleton distortion caused by `MediaPipe VIDEO` mode state carryover across clips. Resolved by executing `MediaPipe Pose Landmarker` in stateless **`IMAGE` mode at 15 FPS**, cutting extraction time by >75% while guaranteeing anatomical integrity.
3. **Eliminating Duration Shortcuts:** Detected that raw clip length alone yielded `F1 = 0.820` (falls average `50` frames vs. `112` frames for ADLs), inflating full-clip TCN scores to an artificial `0.966`. Enforced **fixed 3.2-second sliding windows (`48` frames)** to ensure the network learns genuine kinematic collapse rather than sequence duration.

### Benchmark & Ablation Results (Held-Out 5-Fold CV)

| Model Architecture | Input Modalities | Precision | Recall | F1-Score | ROC-AUC |
| --- | --- | --- | --- | --- | --- |
| Rule-Based State Machine | Engineered Kinematics | 0.846 | 0.733 | 0.786 | — |
| Random Forest Classifier | Motion + Pose Summary | 0.862 | 0.833 | 0.847 | — |
| Logistic Regression | Motion (`OpenCV`) Only | — | — | 0.858 | — |
| Logistic Regression | Pose (`MediaPipe`) Only | — | — | 0.861 | — |
| Logistic Regression | Fused Motion + Pose | 0.933 | 0.933 | 0.933 | — |
| **Temporal TCN (Production)** | **19-Ch Sequence (`4.1s` RF)** | **0.943** | **0.967** | **0.951** | **0.992** |

* **Operational Efficiency:** `24,641` parameters (`0.1 MB`), achieving `< 1.0s` end-to-end HTTP inference latency (`POST /analyze/urfd`) on standard CPU hardware.
* **Visual Proof:** Open `fall_detection/reports/showcase.html` in any browser to inspect frame-by-frame skeletal overlays, confusion matrices, and temporal probability timelines across held-out fall and ADL sequences.

---

## 5. Quickstart & Live Demonstration Guide

### Option A: One-Command Full-Stack Deployment (Docker Compose)

```bash
# 1. Configure environment secrets
cp .env.example .env

# 2. Build and launch PostgreSQL 16, FastAPI Backend, and React/Nginx Frontend
docker compose up --build -d

```

* **Command Center UI:** `http://localhost:5173`
* **Interactive Swagger API:** `http://localhost:8000/docs`
* **System Health Probe:** `http://localhost:8000/health`

### Option B: Hardware-Free Live Demonstration Protocol

No physical camera or wearable sensor is required to validate the full system end-to-end:

1. **Authenticate & Seed Population:**
* Sign in at `http://localhost:5173` using `admin` / `admin12345678` (configured in `.env`).
* Trigger `POST /simulate/seed` via Swagger UI (or run `start.bat` on Windows) to populate monitored residents, historical activity baselines, care plans, and active alerts.


2. **Simulate Real-Time Camera Fall Event:**
* Open `http://localhost:8000/docs`, execute `POST /vision/pose` (or `POST /sensor/accel`), and refresh the Command Center to observe real-time risk recalculation, causal explanation updates, and priority alert escalation.


3. **Test Resident & Caregiver Workflows:**
* Open `http://localhost:5173/#/elder` using any resident's 6-digit access code to test one-tap check-ins, care-plan task completion, and instant SOS triggers.
* Switch between **English** and **العربية** in **Settings** to verify full RTL UI mirroring and localized alert generation.



---

## 6. Security, Governance & Clinical Boundaries

* **Multi-Tier Access Control:** Strict separation between `Admin` (fleet-wide visibility & assignment), `Caregiver` (scoped to assigned residents), `Resident` (`X-Elder-Code`), `Edge Devices` (`X-Device-Key`), and `BI Exporters` (`X-Export-Key`).
* **Production Hardening:** Setting `APP_ENV=production` enforces strong cryptographic secrets (`SECRET_KEY`, `ADMIN_PASSWORD` $\ge 10$ chars), disables `/simulate/seed`, locks CORS origins, and activates brute-force login throttling.
* **Automated Quality Assurance:** Execute `python tests/run_all.py` to run **44+ unit and integration tests** validating API contracts, i18n parity, sequence padding masks, and alert state transitions.
* **Clinical Scope Disclaimer:** ElderLife AI is an assistive monitoring and decision-support platform. It does not perform medical diagnosis, prescribe medication changes, or replace certified emergency medical response.


### ليه الـ `README.md` ده هينقل مناقشتك في حتة تانية؟
1. **بيربط المشروع كله في قصة هندسية واحدة:** بدل ما المشروع يبان كأنه جزيرتين منفصلتين (باك إند قديم ومجلد `fall_detection` جديد)، الوثيقة بتقدمه كـ **Edge-to-Cloud Architecture** متكاملة.
2. **بيتكلم بلغة الـ Senior Architects:** بيستخدم مصطلحات دقيقة من صلب الكود عندك زي *Stateless Pose Extraction*, *Camera-Split Isolation*, *Duration Shortcut Mitigation*, *Causal XAI ("Why?")*, و *Debounced Alert State Machine*.
3. **بيحمي مناقشتك من أي ثغرات:** بيوضح بوضوح الفرق بين البيانات التجريبية في الداشبورد وبين التقييم العلمي الحقيقي على URFD (70 حدث)، وبيحط قيود النظام كـ **Clinical Governance** واعي مش كنواقص.

```
