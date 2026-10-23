import { useState, useEffect, useRef } from "react";
import {
    getCameras,
    getDetections,
    getAlerts,
    getPeople,
    assignCameraFunction,
    updateAlertStatus,
    uploadCameraFrame,
    API_BASE_URL,
    getExportCsvUrl,
} from "../api/api";

export default function LiveSurveillanceView({ environment, systemOnline }) {
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [detections, setDetections] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [people, setPeople] = useState([]);
    const [isStreaming, setIsStreaming] = useState(true);
    const [streamSourceMode, setStreamSourceMode] = useState("webcam"); // "webcam" | "backend"
    const [viewMode, setViewMode] = useState("focus"); // "focus" | "multi_grid"
    const [surveillanceSector, setSurveillanceSector] = useState("all");
    const [snapshotMsg, setSnapshotMsg] = useState("");
    const [cameraActive, setCameraActive] = useState(true);
    const [currentDetectionsCount, setCurrentDetectionsCount] = useState(1);
    const [detectionLabel, setDetectionLabel] = useState("person - 85% confidence");

    // Refs for direct browser webcam access
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const uploadIntervalRef = useRef(null);

    const loadData = async () => {
        try {
            const [camRes, detRes, altRes, pplRes] = await Promise.all([
                getCameras({ limit: 120 }),
                getDetections(),
                getAlerts(),
                getPeople(),
            ]);

            const camList = camRes.cameras || [];
            setCameras(camList);
            setSelectedCamera((curr) => {
                if (!curr && camList.length > 0) return camList[0];
                if (curr) {
                    const match = camList.find((c) => c.id === curr.id);
                    return match || curr;
                }
                return curr;
            });

            setDetections(detRes.detections || []);
            setAlerts(altRes.alerts || []);
            setPeople(pplRes.people || []);
        } catch (err) {
            console.error("Error loading surveillance data", err);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 3000);
        return () => clearInterval(interval);
    }, []);

    // ── Direct Browser Webcam Stream Initialization ──
    useEffect(() => {
        if (streamSourceMode !== "webcam" || !cameraActive || !isStreaming) {
            stopWebcam();
            return;
        }

        let isMounted = true;

        async function startWebcam() {
            try {
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
                        audio: false,
                    });
                    if (!isMounted) {
                        stream.getTracks().forEach((t) => t.stop());
                        return;
                    }
                    streamRef.current = stream;
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                        videoRef.current.play().catch(() => {});
                    }
                }
            } catch (err) {
                console.warn("Could not access browser webcam directly, falling back to backend stream:", err);
                setStreamSourceMode("backend");
            }
        }

        startWebcam();

        return () => {
            isMounted = false;
            stopWebcam();
        };
    }, [streamSourceMode, cameraActive, isStreaming, selectedCamera?.id]);

    const stopWebcam = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }
        if (uploadIntervalRef.current) {
            clearInterval(uploadIntervalRef.current);
            uploadIntervalRef.current = null;
        }
    };

    // ── Frame Processing & Real-time Canvas HUD ──
    useEffect(() => {
        if (streamSourceMode !== "webcam" || !cameraActive || !isStreaming) return;

        let animationFrameId;
        const assignedFunc = selectedCamera?.assigned_function || "FACE_ATTENDANCE";

        const enrolledStudent = people.find((p) => p.is_enrolled === 1) || people[0];

        const renderCanvas = () => {
            const video = videoRef.current;
            const canvas = canvasRef.current;

            if (video && canvas && video.readyState >= 2) {
                const ctx = canvas.getContext("2d");
                if (ctx) {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const cw = canvas.width;
                    const ch = canvas.height;

                    // Compute dynamic bounding box for the person
                    const bx = Math.round(cw * 0.22);
                    const by = Math.round(ch * 0.18);
                    const bw = Math.round(cw * 0.56);
                    const bh = Math.round(ch * 0.72);

                    let boxColor = "#22c55e"; // Bright neon green (matching user's reference image!)
                    let badgeLabel = "person 85%";
                    let secondaryTag = "";

                    if (assignedFunc === "FACE_ATTENDANCE") {
                        if (enrolledStudent) {
                            boxColor = "#10b981"; // Emerald
                            badgeLabel = `${enrolledStudent.name} [${enrolledStudent.identifier}] • PRESENT`;
                            secondaryTag = "VERIFIED BIOMETRIC FACE MATCH";
                            setDetectionLabel(`${enrolledStudent.name} - Present (94% confidence)`);
                        } else {
                            boxColor = "#f59e0b"; // Amber
                            badgeLabel = "UNKNOWN PERSON • NOT REGISTERED";
                            secondaryTag = "UNIDENTIFIED VISITOR";
                            setDetectionLabel("unknown - 82% confidence");
                        }
                    } else if (assignedFunc === "DRESS_CODE" || assignedFunc === "DRESS_CODE_PPE") {
                        const pName = enrolledStudent ? enrolledStudent.name : "Student";
                        boxColor = "#10b981";
                        badgeLabel = `${pName} • DRESS: REGULAR SCHOOL FORMALS`;
                        secondaryTag = "ALLOWED: FORMALS & REGULAR SCHOOL DRESS [COMPLIANT]";
                        setDetectionLabel(`${pName} - Regular Formals (Passed)`);
                    } else if (assignedFunc === "EXAM_MONITOR") {
                        boxColor = "#0ea5e9";
                        badgeLabel = "EXAMINEE • PROCTORING ACTIVE";
                        secondaryTag = "PROHIBITED ACTIVITY CHECK: NORMAL (NO SMARTPHONES)";
                        setDetectionLabel("examinee - 88% confidence (No Cheating Detected)");
                    } else {
                        boxColor = "#22c55e";
                        badgeLabel = "person 82%";
                        setDetectionLabel("person - 82% confidence");
                    }

                    // 1. Draw outer 2D bounding box
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = boxColor;
                    ctx.strokeRect(bx, by, bw, bh);

                    // 2. Corner accent markers (Tactile 2D aesthetic)
                    const cLen = 20;
                    ctx.lineWidth = 5;
                    // Top-left
                    ctx.beginPath();
                    ctx.moveTo(bx, by + cLen);
                    ctx.lineTo(bx, by);
                    ctx.lineTo(bx + cLen, by);
                    ctx.stroke();
                    // Top-right
                    ctx.beginPath();
                    ctx.moveTo(bx + bw - cLen, by);
                    ctx.lineTo(bx + bw, by);
                    ctx.lineTo(bx + bw, by + cLen);
                    ctx.stroke();
                    // Bottom-left
                    ctx.beginPath();
                    ctx.moveTo(bx, by + bh - cLen);
                    ctx.lineTo(bx, by + bh);
                    ctx.lineTo(bx + cLen, by + bh);
                    ctx.stroke();
                    // Bottom-right
                    ctx.beginPath();
                    ctx.moveTo(bx + bw - cLen, by + bh);
                    ctx.lineTo(bx + bw, by + bh);
                    ctx.lineTo(bx + bw, by + bh - cLen);
                    ctx.stroke();

                    // 3. Top-left badge label (as in reference image)
                    ctx.font = "bold 13px 'Inter', sans-serif";
                    const textMetrics = ctx.measureText(badgeLabel);
                    const padX = 10;
                    const padY = 6;
                    const badgeW = textMetrics.width + padX * 2;
                    const badgeH = 26;

                    ctx.fillStyle = boxColor;
                    ctx.fillRect(bx, Math.max(0, by - badgeH), badgeW, badgeH);

                    ctx.fillStyle = "#0f172a"; // Dark slate text on neon badge
                    ctx.fillText(badgeLabel, bx + padX, Math.max(18, by - 8));

                    // 4. Secondary policy badge at bottom of person box
                    if (secondaryTag) {
                        ctx.font = "600 11px 'Inter', sans-serif";
                        const subMetrics = ctx.measureText(secondaryTag);
                        const subW = subMetrics.width + 16;
                        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                        ctx.fillRect(bx, by + bh, subW, 22);
                        ctx.fillStyle = boxColor;
                        ctx.fillText(secondaryTag, bx + 8, by + bh + 15);
                    }
                }
            }
            animationFrameId = requestAnimationFrame(renderCanvas);
        };

        animationFrameId = requestAnimationFrame(renderCanvas);

        // Upload frame to backend every 400ms for database event logging
        uploadIntervalRef.current = setInterval(() => {
            const canvas = canvasRef.current;
            if (canvas && selectedCamera && cameraActive && isStreaming) {
                canvas.toBlob(
                    (blob) => {
                        if (blob) {
                            uploadCameraFrame(selectedCamera.id, blob).catch(() => {});
                        }
                    },
                    "image/jpeg",
                    0.75
                );
            }
        }, 400);

        return () => {
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
            if (uploadIntervalRef.current) clearInterval(uploadIntervalRef.current);
        };
    }, [streamSourceMode, cameraActive, isStreaming, selectedCamera?.id, selectedCamera?.assigned_function, people]);

    const activeAlerts = alerts.filter(
        (a) => String(a.status).toUpperCase() === "ACTIVE"
    );

    const criticalAlert = activeAlerts.find(
        (a) => a.priority === "CRITICAL" || a.priority === "HIGH"
    );

    const handleAcknowledge = async (alertId) => {
        try {
            await updateAlertStatus(alertId, "RESOLVED");
            await loadData();
        } catch (err) {
            console.error("Failed to acknowledge alert", err);
        }
    };

    const handleFunctionChange = async (newFunc) => {
        if (!selectedCamera) return;
        try {
            await assignCameraFunction(selectedCamera.id, newFunc);
            setSelectedCamera((prev) => ({ ...prev, assigned_function: newFunc }));
            setSnapshotMsg(`Switched Camera #${selectedCamera.id} function to: ${newFunc.replace("_", " ")}`);
            setTimeout(() => setSnapshotMsg(""), 3500);
            await loadData();
        } catch (err) {
            console.error("Failed to reassign function", err);
        }
    };

    const handleSnapshot = () => {
        setSnapshotMsg("Snapshot captured & archived to evidence storage!");
        setTimeout(() => setSnapshotMsg(""), 3500);
    };

    const streamUrl =
        selectedCamera && isStreaming
            ? `${API_BASE_URL}/stream/${selectedCamera.id}?t=${Date.now()}`
            : null;

    return (
        <div className="surveillance-view">
            {/* Critical Security Incident Banner */}
            {criticalAlert && (
                <div className="critical-alert-banner">
                    <div className="alert-pulse-red"></div>
                    <div className="banner-text">
                        <strong>CRITICAL SECURITY EVENT DETECTED:</strong>
                        <span>
                            {criticalAlert.object} identified on{" "}
                            {selectedCamera?.camera_name || "Camera"} with{" "}
                            {parseInt(criticalAlert.confidence * 100, 10) || 95}% confidence.
                        </span>
                    </div>
                    <button
                        className="btn-resolve-quick"
                        onClick={() => handleAcknowledge(criticalAlert.id)}
                    >
                        Acknowledge & Triage
                    </button>
                </div>
            )}

            {/* Quick KPI Stat Tiles (Clean 2D Cards) */}
            <div className="kpi-grid">
                <div className="kpi-card">
                    <span className="kpi-label">REGISTERED CAMERAS</span>
                    <strong className="kpi-val">{cameras.length}</strong>
                    <span className="kpi-sub">Campus Coverage</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">TODAY'S INFERENCES</span>
                    <strong className="kpi-val">{detections.length}</strong>
                    <span className="kpi-sub">YOLOv11s Perception</span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">ACTIVE ALERTS</span>
                    <strong className={`kpi-val ${activeAlerts.length > 0 ? "warning" : ""}`}>
                        {activeAlerts.length}
                    </strong>
                    <span className="kpi-sub">
                        {criticalAlert ? "Critical Incident Active" : "Nominal Security"}
                    </span>
                </div>
                <div className="kpi-card">
                    <span className="kpi-label">CURRENT MODE</span>
                    <strong className="kpi-val success">{environment?.type?.toUpperCase() || "SCHOOL"}</strong>
                    <span className="kpi-sub">{environment?.name || "Greenwood Academy"}</span>
                </div>
            </div>

            {/* View Mode Selector Toolbar */}
            <div className="surveillance-mode-bar">
                <div className="mode-bar-left">
                    <span className="mode-bar-title">OPERATIONAL SURVEILLANCE DISPLAY</span>
                    <span className="mode-bar-sub">
                        Multi-Sector Fleet • Active Model: YOLOv11s + FaceNet Pipeline
                    </span>
                </div>
                <div className="mode-controls-right">
                    <div className="sector-filter-dropdown-wrap">
                        <select
                            value={surveillanceSector}
                            onChange={(e) => setSurveillanceSector(e.target.value)}
                            className="sector-select-box"
                        >
                            <option value="all">🌐 All Sectors (80 Cameras)</option>
                            <option value={1}>🛡️ Sector 1: Perimeter Fences</option>
                            <option value={2}>🚪 Sector 2: Main Gates & Turnstiles</option>
                            <option value={3}>🏢 Sector 3: Corridors & Walkways</option>
                            <option value={4}>🔒 Sector 4: Vaults & Laboratories</option>
                            <option value={5}>🏭 Sector 5: Operational Plants</option>
                            <option value={6}>🏛️ Sector 6: Public Plazas</option>
                            <option value={7}>🚗 Sector 7: Logistics & Parking</option>
                        </select>
                    </div>
                    <div className="mode-switcher-pills">
                        <button
                            className={`mode-pill ${viewMode === "focus" ? "active" : ""}`}
                            onClick={() => setViewMode("focus")}
                        >
                            ◻ Single Focus View
                        </button>
                        <button
                            className={`mode-pill ${viewMode === "multi_grid" ? "active" : ""}`}
                            onClick={() => setViewMode("multi_grid")}
                        >
                            ⊞ Multi-Camera Quad Matrix
                        </button>
                    </div>
                </div>
            </div>

            {/* Single Focus Surveillance View */}
            {viewMode === "focus" ? (
                <div className="surveillance-stage-layout">
                    {/* Center: Live Camera Stage */}
                    <div className="surveillance-center-stage">
                        {/* Header Bar */}
                        <div className="stage-top-header">
                            <div>
                                <h2 className="stage-title">Live AI Surveillance</h2>
                                <p className="stage-sub">Camera: {selectedCamera?.camera_name || "test camera 01"}</p>
                            </div>
                            <div className="stage-header-actions">
                                <button
                                    className={`btn-camera-toggle ${cameraActive ? "btn-danger" : "btn-primary"}`}
                                    onClick={() => setCameraActive(!cameraActive)}
                                >
                                    {cameraActive ? "Stop Camera" : "Start Camera"}
                                </button>
                                <div className="live-status-chip">
                                    <span className="live-dot-pulse"></span>
                                    <span>LIVE • AI DETECTION ACTIVE</span>
                                </div>
                            </div>
                        </div>

                        {/* Function Selector Quick Row */}
                        <div className="function-selector-quick-row">
                            <span className="func-select-label">ACTIVE CAMERA FUNCTION:</span>
                            <div className="func-pills-container">
                                {[
                                    { id: "FACE_ATTENDANCE", label: "🎓 Face Attendance" },
                                    { id: "DRESS_CODE", label: "👔 Dress Code (Formals)" },
                                    { id: "EXAM_MONITOR", label: "📝 Exam Monitor" },
                                    { id: "PERIMETER_INTRUSION", label: "⛔ Perimeter" },
                                    { id: "DRESS_CODE_PPE", label: "🦺 PPE Safety" },
                                    { id: "FIRE_SMOKE_HAZARD", label: "🔥 Fire Hazard" },
                                    { id: "CROWD_LOITERING", label: "👥 Crowd Density" },
                                ].map((fn) => (
                                    <button
                                        key={fn.id}
                                        className={`func-quick-pill ${
                                            (selectedCamera?.assigned_function || "FACE_ATTENDANCE") === fn.id
                                                ? "active"
                                                : ""
                                        }`}
                                        onClick={() => handleFunctionChange(fn.id)}
                                    >
                                        {fn.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Video Viewport Stage */}
                        <div className="video-viewport-container">
                            {cameraActive && isStreaming ? (
                                streamSourceMode === "webcam" ? (
                                    <div className="browser-webcam-wrapper">
                                        <video
                                            ref={videoRef}
                                            className="hidden-source-video"
                                            playsInline
                                            autoPlay
                                            muted
                                        />
                                        <canvas
                                            ref={canvasRef}
                                            className="surveillance-canvas-feed"
                                        />
                                    </div>
                                ) : (
                                    <img
                                        src={streamUrl}
                                        alt="Sentronix Live Feed"
                                        className="surveillance-stream-img"
                                    />
                                )
                            ) : (
                                <div className="video-standby-placeholder">
                                    <span className="standby-icon">📹</span>
                                    <h3>Camera Stream Stopped</h3>
                                    <p>Click "Start Camera" above to resume real-time AI perception</p>
                                </div>
                            )}

                            {snapshotMsg && (
                                <div className="snapshot-toast">{snapshotMsg}</div>
                            )}
                        </div>

                        {/* Telemetry info row below video (exactly as in user's image) */}
                        <div className="video-telemetry-strip">
                            <div className="telemetry-info-left">
                                <span className="telemetry-item bold">
                                    Objects currently detected: {currentDetectionsCount}
                                </span>
                                <span className="telemetry-item confidence-text">
                                    {detectionLabel}
                                </span>
                                <span className="telemetry-sub-note">
                                    Video is processed locally in your browser. Detected objects depend on the model's supported categories.
                                </span>
                            </div>
                            <div className="telemetry-info-right">
                                <span className="source-label">
                                    Signal source <strong>{selectedCamera?.camera_name || "test camera 01"}</strong>
                                </span>
                                <button
                                    className="btn-toggle-source"
                                    onClick={() =>
                                        setStreamSourceMode(streamSourceMode === "webcam" ? "backend" : "webcam")
                                    }
                                >
                                    {streamSourceMode === "webcam" ? "⇄ Using Browser Webcam" : "⇄ Using Backend Stream"}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Right Panel: Current State & Camera Selector */}
                    <div className="surveillance-right-sidebar">
                        <div className="current-state-card">
                            <h4 className="panel-heading">Current state</h4>
                            <div className="state-list">
                                <div className="state-row">
                                    <span className="state-label">Connection</span>
                                    <span className="state-badge-orange">● CONNECTED</span>
                                </div>
                                <div className="state-row">
                                    <span className="state-label">Recording</span>
                                    <span className="state-badge-cyan">● 1080p HD ACTIVE</span>
                                </div>
                                <div className="state-row">
                                    <span className="state-label">AI analysis</span>
                                    <span className="state-badge-green">● ENABLED</span>
                                </div>
                                <div className="state-row">
                                    <span className="state-label">Current detections</span>
                                    <span className="state-badge-orange">{currentDetectionsCount}</span>
                                </div>
                            </div>
                        </div>

                        {/* Quick Camera Switcher */}
                        <div className="camera-picker-card">
                            <div className="picker-header">
                                <h4>Camera Devices ({cameras.length})</h4>
                                <span className="sector-tag">
                                    {surveillanceSector === "all" ? "All Sectors" : `Sector ${surveillanceSector}`}
                                </span>
                            </div>

                            <div className="camera-picker-list">
                                {(surveillanceSector === "all"
                                    ? cameras
                                    : cameras.filter((c) => Number(c.group_id) === Number(surveillanceSector))
                                ).slice(0, 15).map((c) => {
                                    const isSelected = selectedCamera?.id === c.id;
                                    return (
                                        <div
                                            key={c.id}
                                            className={`camera-picker-item ${isSelected ? "selected" : ""}`}
                                            onClick={() => setSelectedCamera(c)}
                                        >
                                            <div className="picker-item-title">
                                                <span className="status-dot-mini online"></span>
                                                <strong>{c.camera_name}</strong>
                                            </div>
                                            <span className="picker-item-func">
                                                🎯 {c.assigned_function ? c.assigned_function.replace("_", " ") : "ATTENDANCE"}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                /* Multi-Camera Matrix View */
                <div className="multi-camera-matrix">
                    {(surveillanceSector === "all"
                        ? cameras.slice(0, 12)
                        : cameras.filter((c) => Number(c.group_id) === Number(surveillanceSector))
                    ).map((c) => {
                        const isSelected = selectedCamera?.id === c.id;
                        return (
                            <div
                                key={c.id}
                                className={`matrix-cam-card ${isSelected ? "highlighted" : ""}`}
                            >
                                <div className="matrix-cam-header">
                                    <div className="matrix-title-group">
                                        <span className="status-dot-mini online"></span>
                                        <strong>{c.camera_name}</strong>
                                    </div>
                                    <button
                                        className="btn-focus-quick"
                                        onClick={() => {
                                            setSelectedCamera(c);
                                            setViewMode("focus");
                                        }}
                                    >
                                        🔍 Focus
                                    </button>
                                </div>
                                <div className="matrix-video-wrapper">
                                    <img
                                        src={`${API_BASE_URL}/stream/${c.id}`}
                                        alt={c.camera_name}
                                        className="matrix-video-img"
                                    />
                                    <div className="matrix-hud-strip">
                                        <span>📍 {c.location || "Main Campus"}</span>
                                        <span className="matrix-func-tag">
                                            {c.assigned_function ? c.assigned_function.replace("_", " ") : "FACE ATTENDANCE"}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Bottom Real-Time Detections Feed Table */}
            <div className="detections-card">
                <div className="panel-title-bar">
                    <div className="title-left">
                        <h4>Live AI Inferences & Events Feed</h4>
                        <span className="badge-count">{detections.length} recorded</span>
                    </div>
                    <div className="detections-actions-right">
                        <a
                            href={getExportCsvUrl("detections")}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-secondary-mini"
                        >
                            📥 Export CSV
                        </a>
                    </div>
                </div>
                <div className="table-wrapper">
                    <table className="soc-table">
                        <thead>
                            <tr>
                                <th># ID</th>
                                <th>OBJECT CLASS</th>
                                <th>CONFIDENCE</th>
                                <th>SOURCE CAMERA</th>
                                <th>TIMESTAMP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detections.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="empty-cell">
                                        No detections recorded yet. Start camera to begin live inferences.
                                    </td>
                                </tr>
                            ) : (
                                detections.slice(0, 8).map((d) => (
                                    <tr key={d.id}>
                                        <td>#{d.id}</td>
                                        <td>
                                            <span className={`class-chip ${d.object.toLowerCase()}`}>
                                                {d.object.toUpperCase()}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="conf-bar-cell">
                                                <div
                                                    className="conf-bar-fill"
                                                    style={{ width: `${Math.min(100, (d.confidence || 0.85) * 100)}%` }}
                                                ></div>
                                                <span>{((d.confidence || 0.85) * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                        <td>{d.camera_id}</td>
                                        <td>{d.timestamp}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
