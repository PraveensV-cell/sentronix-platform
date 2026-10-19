# Sentronix AI — Intelligent Surveillance & Safety Operations Platform

> **An Enterprise-Grade AI Surveillance, Face Recognition Attendance & Safety Command Center**

---

## 1. What Sentronix Is
**Sentronix AI** is an intelligent AI-powered surveillance and safety operations platform designed to observe, analyze, detect, track, and interpret real-time events across diverse environments. 

Rather than functioning as a passive video recorder or a generic chatbot, Sentronix functions as an autonomous **surveillance operations assistant (NOC/SOC command center)** that integrates computer vision, face identification, automated attendance tracking, configurable safety rule evaluation, incident triage, and operational reporting.

---

## 2. Architecture

```mermaid
flowchart TD
    subgraph UI ["Command Center Frontend (React 19 + TypeScript + Vite + Tailwind)"]
        Auth["Auth & Development Mock OTP"]
        ModeSelect["Environment & Feature Selector"]
        LiveView["Live Surveillance & AI HUD"]
        Attendance["Campus Attendance Center"]
        Alerts["Incident & Alert Triage"]
        People["People & Facial Enrollment"]
        Rules["Safety Policy & Rule Engine"]
        Analytics["Reports & Analytics"]
        Assistant["Sentronix AI Operator Assistant"]
    end

    subgraph API ["Sentronix Core API Layer (FastAPI)"]
        RouterAuth["Auth & User Registry"]
        RouterCam["Camera & MJPEG Stream Engine"]
        RouterAttend["Attendance & Deduplication"]
        RouterRules["Rule Engine & Zone Evaluation"]
        RouterAssist["Assistant Tool Calling Engine"]
    end

    subgraph Perception ["Vision & Perception Pipeline"]
        YOLO["YOLOv8 / YOLO11 Deep Learning Detector"]
        FaceEngine["OpenCV Face Detector & Feature Matcher"]
        Tracker["Centroid Tracking & Presence Duration"]
        RuleEval["Safety & Policy Evaluator"]
    end

    subgraph Data ["Persistence Layer"]
        DB[(PostgreSQL / SQLite)]
        EvidenceFS["Local Evidence & Snapshot Store"]
    end

    UI <--> API
    API <--> Perception
    API <--> Data
    Perception --> Data
```

---

## 3. Technology Stack

* **Backend & API**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
* **Computer Vision & Deep Learning**: PyTorch (with CUDA acceleration), Ultralytics YOLOv8 / YOLO11, OpenCV (Haar Cascades / DNN Face Detection), NumPy.
* **Database & ORM**: SQLite (instant zero-dependency local runs and demos) / PostgreSQL (enterprise Docker deployment), SQLAlchemy.
* **Frontend**: React 19, TypeScript, Vite, Recharts, Axios, CSS3 Surveillance Theme.
* **Containerization & DevOps**: Docker, Docker Compose, Git, Pytest / Unittest.

---

## 4. Folder Structure

```
sentronix-platform/
├── ml-platform/
│   ├── api/                     # Unified 90+ endpoint FastAPI backend
│   │   ├── auth_api.py          # User registration, mock OTP & JWT login
│   │   ├── environment_api.py   # Mode selection & feature toggles
│   │   ├── camera_stream.py     # Live MJPEG streaming with AI bounding boxes
│   │   ├── camera_api.py        # Camera hardware registration
│   │   ├── people_api.py        # Students, staff & facial enrollment
│   │   ├── attendance_api.py    # Presence verification & deduplication
│   │   ├── rules_api.py         # Safety & dress code policies
│   │   ├── assistant_api.py     # AI operator tool-calling assistant
│   │   ├── vision_engine.py     # YOLO + OpenCV face detection engine
│   │   └── main.py              # Main API router
│   ├── dashboard/               # React 19 + TypeScript + Vite frontend
│   │   ├── src/components/      # Navbar, Sidebar, AIAssistantWidget
│   │   ├── src/pages/           # LiveSurveillance, Attendance, Alerts, etc.
│   │   └── src/api/             # Typed API client
│   ├── database/                # SQLite relational database & schema
│   │   ├── database_schema.py   # Schema definitions & migrations
│   │   └── sentronix.db         # Persistent storage
│   ├── inference/               # Standalone tracking & detector scripts
│   └── training/                # YOLO custom training scripts & configs
├── services/                    # Enterprise microservices stack (API Gateway, etc.)
├── tests/                       # Automated integration & full-stack test suite
├── runs/detect/                 # Trained YOLO weights & validation curves
├── start_sentronix.bat          # Single-click Windows launcher
├── start_sentronix.py           # Cross-platform startup script
└── requirements.txt             # Python dependencies
```

---

## 5. Prerequisites

* Windows 10/11, macOS, or Linux.
* Python 3.10+ (Python 3.11 recommended).
* Node.js v18+ and npm.
* Dedicated GPU optional (CUDA enabled automatically if NVIDIA GPU is detected).

---

## 6. Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/PraveensV-cell/sentronix-platform.git
   cd sentronix-platform
   ```

2. **Setup Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup Frontend Dependencies**:
   ```bash
   cd ml-platform/dashboard
   npm install
   cd ../..
   ```

---

## 7. Environment Variables

Create `.env` in `sentronix-platform/ml-platform/` or configure via UI:
```env
APP_NAME=Sentronix AI Platform
PORT=8000
ENVIRONMENT=development
JWT_SECRET=sentronix_secret_key_12345
DATABASE_TYPE=sqlite
DATABASE_PATH=database/sentronix.db
```

---

## 8. Database Setup

To initialize all 13 relational tables and seed default School/College safety policies:
```bash
python ml-platform/database/database_schema.py
```

---

## 9. Running with Single-Click Launcher

### Windows
Double-click `start_sentronix.bat` or run:
```powershell
python start_sentronix.py
```
This automatically:
1. Verifies and migrates the database schema.
2. Starts the FastAPI backend at `http://127.0.0.1:8000`.
3. Starts the React command center at `http://localhost:5173`.
4. Opens your default web browser directly to the login screen.

---

## 10. Running Manually (Without Docker)

**Terminal 1 (Backend)**:
```bash
cd ml-platform
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend)**:
```bash
cd ml-platform/dashboard
npm run dev
```

---

## 11. AI Model Setup

Sentronix includes support for multiple YOLO variants:
* `yolo11n.pt` (Standard Nano object detector — Fast real-time inference)
* `yolo11s.pt` (Standard Small object detector — Higher accuracy)
* `runs/detect/yolo26n-dfire-2/weights/best.pt` (Custom trained fire and hazard model)

Weights are dynamically selected by `ml-platform/api/vision_engine.py`.

---

## 12. YOLO Model Download

If weights are missing, Ultralytics downloads them automatically upon first inference. You can also manually download them:
```bash
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
```

---

## 13. CPU / GPU Setup

In `ml-platform/api/vision_engine.py`, PyTorch automatically verifies CUDA availability:
* If NVIDIA CUDA is detected, inference runs on GPU (`device='cuda:0'`).
* Otherwise, it runs seamlessly on CPU with optimized frame sampling.

---

## 14. Webcam Setup

* By default, Camera 1 is mapped to camera index `0` (built-in or USB webcam).
* You can change camera sources anytime in **Camera Devices** view.

---

## 15. Video File Setup

To test with pre-recorded surveillance video:
1. Place your MP4 file in `ml-platform/`.
2. Register a camera with source `sample.mp4`.

---

## 16. RTSP Setup

To connect IP cameras, specify the RTSP stream URL in the Camera Manager:
`rtsp://admin:password@192.168.1.100:554/stream1`

---

## 17. Face Enrollment

1. Navigate to **People & Faces** tab.
2. Click **+ Register Person** (specify Name, Student/Staff ID, Role, Department).
3. Click **Capture & Enroll Face** to extract facial vector embeddings into the database.

---

## 18. Attendance Configuration

1. Student enters the surveillance camera zone.
2. The AI Vision Engine performs person and face detection.
3. Facial feature matching compares the detected face against enrolled profiles ($>70\%$ confidence threshold).
4. If presence persists $> 3$ seconds, an attendance log is created with duplicate suppression.
5. Check-ins before 09:00 AM are marked `PRESENT`; arrivals after 09:00 AM are flagged as `LATE`.

---

## 19. Rule Configuration

In **Policy & Rules** tab:
* **Restricted Zone Access**: Triggers alert when a person enters laboratory/server areas.
* **Prohibited Weapons**: Triggers `CRITICAL` alarm on knife, pistol, or weapon-like objects.
* **Fire & Smoke**: Triggers immediate emergency alert.

---

## 20. Dress Code Configuration

* Sentronix separates verified classes from specialized uniform requirements.
* If custom fine-tuned weights for uniforms are not loaded, the system explicitly displays:
  **"⚠️ Custom Model Required"**
  preventing false claims and maintaining architectural integrity.

---

## 21. Creating Custom Environments

1. On the **Mode Selection** screen, click **+ Custom Environment**.
2. Enter Name, Facility Type (Hospital, Industry, Office, Custom), and Location.
3. Toggle enabled surveillance modules (Face detection, attendance, alerts, etc.).
4. Click **Enter Surveillance Command Center**.

---

## 22. Storage Configuration

* Digital evidence, snapshots, and attendance proof are archived locally under `storage/` and cataloged in the SQLite/PostgreSQL `evidence_snapshot` column.

---

## 23. Testing

Run the full end-to-end integration test suite:
```bash
python -m unittest tests/test_sentronix_fullstack.py
```
Validates:
* Root health & versioning
* Registration & mock OTP verification
* JWT login & RBAC
* Environment feature toggling
* Camera registration
* Person & facial enrollment
* Attendance deduplication logic
* Safety rule toggling
* Alert resolution workflow
* AI Assistant tool-calling queries

---

## 24. Troubleshooting

* **Camera feed shows standby**: The system features an automatic fallback to an animated high-fidelity surveillance simulation stream if no physical USB webcam is attached.
* **Vite build warnings**: Vite chunk size warnings can be disregarded or optimized via dynamic imports.

---

## 25. Production Deployment

To run in Docker Compose:
```bash
docker compose up --build
```
This boots all backend microservices, PostgreSQL, Redis, RabbitMQ, and the frontend container.

---

**Prepared by Praveen S — Sentronix AI Surveillance & Safety Platform**
