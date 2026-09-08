# AI-Driven Continuous Authentication Using Explainable Transformers and Behavioral Biometrics

> **M.Tech Dissertation Research Project**  
> A production-grade, end-to-end continuous biometric authentication system powered by deep Explainable Transformers, sliding-window temporal inference, and privacy-preserving behavioral kinematics (keystroke dynamics and mouse trajectories).

---

## 📌 Abstract & Research Objective

Traditional authentication mechanisms (passwords, SMS OTPs, and one-time biometrics like fingerprint/facial recognition) verify identity solely at the perimeter. Once an initial session is authorized, the session remains vulnerable to session hijacking, device theft, shoulder surfing, and insider threats.

This research project introduces an **AI-driven continuous authentication framework** that continuously monitors user interaction patterns in real time without interrupting regular workflow. By processing sequential streams of **Keystroke Dynamics** and **Mouse Kinematics** through an **Explainable PyTorch Transformer**, the system continuously classifies the active user into one of three dynamic states:

1. **`LEGITIMATE USER`** (Confidence $\ge 80\%$) — Interaction dynamics align with the verified profile.
2. **`SUSPICIOUS USER`** ($50\% \le \text{Confidence} < 80\%$) — Minor behavioral anomaly detected; flags warnings.
3. **`POTENTIAL INTRUDER`** ($\text{Confidence} < 50\%$) — Severe divergence from behavioral baseline; triggers intrusion alerts.

To guarantee trustworthy AI in cybersecurity operations, the system integrates **Explainable AI (XAI)** featuring self-attention weight extraction across temporal tokens and gradient-based feature attribution.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Client ["Client Browser (React + Vite + Tailwind CSS)"]
        UI["Cybersecurity Research Dashboard"]
        Track["useBehaviorTracking Hook"]
        Sensors["Keystroke & Mouse Event Listeners"]
        Buffer["Sliding Batch Buffer (3.5s Flushes)"]
        
        Sensors --> Track --> Buffer -->|REST API Batches| UI
    end

    subgraph Backend ["FastAPI Microservice (Python 3.11)"]
        Router["API Gateway (/api/...)"]
        AuthSvc["JWT Auth & Session Manager"]
        FeatEng["Sliding-Window Feature Extractor"]
        XAISvc["Explainability & Attention Engine"]
        Inference["PyTorch Transformer Inference Engine"]
        
        Router --> AuthSvc
        Router --> FeatEng --> Inference --> XAISvc
    end

    subgraph Storage ["Persistent Storage"]
        DB[("Neon PostgreSQL / SQLite DB")]
        Checkpoint[("Transformer Checkpoint (.pt)")]
    end

    Buffer -.->|HTTP POST /api/behavior/...| Router
    Inference -.->|Load Weights| Checkpoint
    Router <--> DB
```

---

## 🔬 Behavioral Biometrics Specification

The system implements a **privacy-first biometric architecture**. At no point are sensitive passwords, form contents, or raw text strings stored or transmitted. Only high-resolution temporal dynamics and kinematics are captured:

### 1. Keystroke Dynamics
* **Key Hold Duration ($H_i$):** Milliseconds elapsed between `keydown` and `keyup` ($T_{\text{release}} - T_{\text{press}}$).
* **Flight Time ($F_i$):** Latency between releasing key $i-1$ and pressing key $i$ ($T_{\text{press}, i} - T_{\text{release}, i-1}$).
* **Typing Speed / Rhythm:** Interaction cadence calculated in characters per second over sliding windows.
* **Key Category:** Behavioral grouping (`ALPHANUMERIC`, `MODIFIER`, `SPACE`, `BACKSPACE`, `ENTER`).

### 2. Mouse Kinematics
* **Cursor Velocity & Distance:** Euclidean displacement divided by elapsed millisecond intervals ($\Delta d / \Delta t$).
* **Trajectory Curvature & Acceleration:** Angular deviation ($\Delta \theta = |\theta_i - \theta_{i-1}|$) and rate of velocity change.
* **Click Duration & Frequency:** Hold latency of mouse press-to-release and clicks per second.
* **Scroll Dynamics:** Magnitude and frequency of mouse wheel interaction events.

---

## 🧠 Transformer Model Architecture

```text
Input Behavioral Sequence [Batch, Window_Size, 16 Features]
                   │
                   ▼
       Linear Projection Embedding (d_model = 64)
                   │
                   ▼
     Sinusoidal Positional Encoding (Temporal Order)
                   │
                   ▼
     Transformer Encoder (2 Layers, 4 Attention Heads)
    ├── Multi-Head Self-Attention (Extracted for XAI)
    ├── Layer Normalization & Residual Connection
    └── Feed-Forward Network (dim_feedforward = 128)
                   │
                   ▼
       Self-Attention Sequence Pooling
                   │
                   ▼
    Multi-Layer Perceptron (Dropout = 0.1, ReLU)
                   │
                   ▼
       Sigmoid Output [0.0 to 1.0 Confidence]
```

### Configurable Hyperparameters
| Parameter | Default Value | Description |
|---|---|---|
| `input_dim` | 16 | Number of statistical biometric features |
| `d_model` | 64 | Latent embedding dimensionality |
| `nhead` | 4 | Number of multi-head self-attention heads |
| `num_layers` | 2 | Transformer encoder depth |
| `window_size` | 40 | Number of raw events per behavioral window |
| `overlap_ratio`| 0.50 (50%) | Sliding window step overlap |
| `optimizer` | AdamW | Weight decay = $1\times 10^{-4}$, LR = $1\times 10^{-3}$ |

---

## 📊 Biometric Evaluation Metrics

The experimental evaluation pipeline (`ml/evaluate.py`) computes research-standard biometric verification metrics:

* **Accuracy, Precision, Recall, and F1-Score**
* **False Acceptance Rate (FAR):** Rate at which unauthorized impostors are mistakenly accepted.
* **False Rejection Rate (FRR):** Rate at which the legitimate user is incorrectly rejected.
* **Equal Error Rate (EER):** Point where FAR equals FRR, defining baseline biometric discriminability.
* **ROC-AUC:** Area under the Receiver Operating Characteristic curve.

Evaluation curves and metrics reports are generated automatically to `ml/saved_models/`:
- `evaluation_report.json`
- `roc_curve.png`
- `eer_plot.png`

---

## 🚀 Step-by-Step Execution Guide

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm
- Git

### 1. Backend Setup & Local Server
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Run automated tests
pytest backend/tests/test_verification.py -v

# Start FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API Swagger documentation will be available at: **`http://127.0.0.1:8000/docs`**

### 2. Frontend Dashboard Setup
```bash
cd frontend
npm install
npm run dev
```
Open your browser at **`http://localhost:5173`** to access the research dashboard.

### 3. Machine Learning Training & Evaluation
```bash
# Train the Transformer model on session-isolated behavioral data
python ml/train.py --epochs 15 --batch-size 32

# Evaluate biometric performance (EER, FAR, FRR, ROC-AUC)
python ml/evaluate.py
```

---

## 🌐 Production Deployment Architecture

```text
Frontend   -> Vercel (Static SPA built with Vite)
Backend    -> Railway (Docker container running FastAPI)
Database   -> Neon PostgreSQL (Serverless cloud PostgreSQL)
```

### 1. Database Deployment (Neon PostgreSQL)
1. Provision a serverless PostgreSQL instance on [Neon](https://neon.tech).
2. Copy the connection string (e.g. `postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require`).

### 2. Backend Deployment (Railway)
1. Create a new project in Railway connected to this GitHub repository.
2. Configure environment variables in Railway:
   * `DATABASE_URL`: Your Neon PostgreSQL connection string.
   * `SECRET_KEY`: A secure random JWT signing key.
   * `CORS_ORIGINS`: `["https://*.vercel.app","http://localhost:5173"]`
3. Railway automatically builds using the root `Dockerfile` and deploys the FastAPI backend.

### 3. Frontend Deployment (Vercel)
1. Import the repository into [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Set Environment Variable:
   * `VITE_API_URL`: Your deployed Railway backend URL (e.g. `https://continuous-auth-production.up.railway.app/api`).
4. Deploy!

---

## 🔒 Security & Privacy Guarantees
* **Zero Character Ingestion:** Input text is never recorded, preventing credential or private data leakage.
* **Cryptographic Password Hashing:** Direct bcrypt salt rounds protect user credentials.
* **Stateless JWT Authorization:** Bearer tokens authenticate every API request.
* **Session Integrity:** Active tracking sessions enforce isolated temporal windows and stateful lifecycle controls.