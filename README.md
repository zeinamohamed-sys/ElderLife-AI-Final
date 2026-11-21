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
